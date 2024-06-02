from bs4 import BeautifulSoup
import pandas as pd
import requests
import plotly.express as px
import streamlit as st
import warnings

warnings.filterwarnings('ignore')

st.set_page_config(layout='wide')

st.title('DASHBOARD DE VENTAS :shopping_trolley:')

url = 'https://ahcamachod.github.io/productos'

response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')
datos = pd.read_json(soup.pre.contents[0])
datos['Fecha de Compra'] = pd.to_datetime(datos['Fecha de Compra'],format='%d/%m/%Y')

regiones_dict = {'Bogotá':'Andina', 'Medellín':'Andina', 'Cali':'Pacífica', 'Pereira':'Andina',    'Barranquilla':'Caribe', 'Cartagena':'Caribe','Cúcuta':'Andina', 'Bucaramanga':'Andina', 'Riohacha':'Caribe', 'Santa Marta':'Caribe', 'Leticia':'Amazónica', 'Pasto':'Andina','Manizales':'Andina', 'Neiva':'Andina', 'Villavicencio':'Orinoquía', 'Armenia':'Andina', 'Soacha':'Andina','Valledupar':'Caribe', 'Inírida':'Amazónica'}

datos['Región'] = datos['Lugar de Compra'].map(regiones_dict)

datos['Año'] = datos['Fecha de Compra'].dt.year

######## Sidebar para usar en la API #########
regiones = ['Colombia','Caribe','Andina','Pacífica','Orinoquía','Amazónica']

st.sidebar.title('Filtro')
region = st.sidebar.selectbox('Región',regiones)
if region == 'Colombia':
  datos = datos.loc[datos['Región'] != "Colombia"]
else:
  datos = datos.loc[datos['Región'] == region]

todos_anos = st.sidebar.checkbox('Datos de todo el periodo', value=True)
if todos_anos:
  datos = datos
else:
  ano = st.sidebar.slider('Año',2020,2023)
  datos = datos.loc[datos['Año'] == ano]

filtro_vendedores = st.sidebar.multiselect('Vendedores', datos.Vendedor.unique())
if filtro_vendedores:
  datos = datos[datos['Vendedor'].isin(filtro_vendedores)]

### Funciones
def formato_numero(valor, prefijo=''):
  for unidad in ['','mil']:
    if valor < 1000:
      return f'{prefijo} {valor:.2f} {unidad}'
    valor /= 1000
  return f'{prefijo} {valor:.2f} millones'

## Cálculos

# st.metric('Facturación',datos['Precio'].sum())
# st.metric('Cantidad de ventas',datos.shape[0])
#### FACTURACION

fact_ciudades = datos.groupby('Lugar de Compra')[['Precio']].sum()
fact_ciudades = datos.drop_duplicates(subset='Lugar de Compra')[['Lugar de Compra','lat','lon']].merge(fact_ciudades,left_on='Lugar de Compra',right_index=True).sort_values('Precio', ascending=False)

fact_mensual = datos.set_index('Fecha de Compra').groupby(pd.Grouper(freq='ME'))['Precio'].sum().reset_index()
fact_mensual['Año'] = fact_mensual['Fecha de Compra'].dt.year
fact_mensual['Mes'] = fact_mensual['Fecha de Compra'].dt.month_name('es_MX.UTF-8')

fact_cat = datos.groupby('Categoría del Producto')[['Precio']].sum().sort_values('Precio',ascending=False)

#### Cantidad de Ventas ################ Actividad de práctica

ventas_ciudades = datos.groupby('Lugar de Compra')[['Precio']].count()
ventas_ciudades = datos.drop_duplicates(subset='Lugar de Compra')[['Lugar de Compra','lat','lon']].merge(ventas_ciudades,left_on='Lugar de Compra',right_index=True).sort_values('Precio', ascending=False)
ventas_ciudades.rename(columns={'Precio':'Cantidad'}, inplace=True)

ventas_mensual = datos.set_index('Fecha de Compra').groupby(pd.Grouper(freq='ME'))['Precio'].count().reset_index()
ventas_mensual['Año'] = ventas_mensual['Fecha de Compra'].dt.year
ventas_mensual['Mes'] = ventas_mensual['Fecha de Compra'].dt.month_name('es_MX.UTF-8')
ventas_mensual.rename(columns={'Precio':'Cantidad'}, inplace=True)

ventas_cat = datos.groupby('Categoría del Producto')[['Precio']].count().sort_values('Precio',ascending=False)
ventas_cat.rename(columns={'Precio':'Cantidad'}, inplace=True)

####Vendedores

vendedores = pd.DataFrame(datos.groupby('Vendedor')['Precio'].agg(['sum','count']))

## Gráficas

fig_fact_mapa = px.scatter_geo(fact_ciudades, lat='lat',lon='lon', scope='south america', size='Precio', template='seaborn', hover_name='Lugar de Compra', hover_data={'lat':False,'lon':False}, title='Facturación por Ciudad')
fig_fact_mapa.update_geos(fitbounds='locations')

fig_fact_mensual = px.line(fact_mensual, x='Mes',y='Precio', markers=True, range_y=(0,fact_mensual.max()), color='Año', line_dash='Año',title='Facturación mensual')
fig_fact_mensual.update_layout(yaxis_title='Facturación')

fig_fact_ciudades= px.bar(fact_ciudades.head(), x='Lugar de Compra', y='Precio', text_auto=True, title='Top ciudades (Facturación)')
fig_fact_ciudades.update_layout(yaxis_title='Facturación')

fig_fact_cat = px.bar(fact_cat, text_auto=True, title='Facturación por categoría')
fig_fact_cat.update_layout(yaxis_title='Facturación')

###### Fig cantidad de ventas ############### Actividad de práctica

fig_ventas_mapa = px.scatter_geo(ventas_ciudades, lat='lat',lon='lon', scope='south america', size='Cantidad', template='seaborn', hover_name='Lugar de Compra', hover_data={'lat':False,'lon':False}, title='Ventas por Ciudad')
fig_ventas_mapa.update_geos(fitbounds='locations')

fig_ventas_mensual = px.line(ventas_mensual, x='Mes',y='Cantidad', markers=True, range_y=(0,ventas_mensual.max()), color='Año', line_dash='Año',title='Ventas mensuales')
fig_ventas_mensual.update_layout(yaxis_title='Ventas')

fig_ventas_ciudades= px.bar(ventas_ciudades.head(), x='Lugar de Compra', y='Cantidad', text_auto=True, title='Top ciudades (Cantidad de ventas)')
fig_ventas_ciudades.update_layout(yaxis_title='Ventas')

fig_ventas_cat = px.bar(ventas_cat, text_auto=True, title='Ventas por categoría')
fig_ventas_cat.update_layout(yaxis_title='Ventas')

### Layout

tab1, tab2, tab3 = st.tabs(['Facturación','Cantidad de ventas','Vendedores'])

with tab1:
  col1,col2 = st.columns(2)
  with col1:
    st.metric('Facturación',formato_numero(datos['Precio'].sum(),'COP'))
    st.plotly_chart(fig_fact_mapa, use_container_width=True)
    st.plotly_chart(fig_fact_ciudades, use_container_width=True)

  with col2:
    st.metric('Cantidad de ventas',formato_numero(datos.shape[0]))
    st.plotly_chart(fig_fact_mensual,use_container_width=True)
    st.plotly_chart(fig_fact_cat, use_container_width=True)

with tab2:
  col1,col2 = st.columns(2)
  with col1:
    st.metric('Facturación',formato_numero(datos['Precio'].sum(),'COP'))
    st.plotly_chart(fig_ventas_mapa, use_container_width=True)
    st.plotly_chart(fig_ventas_ciudades, use_container_width=True)

  with col2:
    st.metric('Cantidad de ventas',formato_numero(datos.shape[0])) 
    st.plotly_chart(fig_ventas_mensual,use_container_width=True)
    st.plotly_chart(fig_ventas_cat, use_container_width=True)

with tab3:
  ct_vendedores = st.number_input('Cantidad de vendedores',2,10,5)
  col1,col2 = st.columns(2)
  with col1:
    st.metric('Facturación',formato_numero(datos['Precio'].sum(),'COP'))    
    fig_fact_vend = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(ct_vendedores), x='sum' , y=vendedores[['sum']].sort_values('sum', ascending=False).head(ct_vendedores).index,text_auto=True, title= f'Top {ct_vendedores} vendedores (Facturación)')
    st.plotly_chart(fig_fact_vend)

  with col2:
    st.metric('Cantidad de ventas',formato_numero(datos.shape[0]))
    fig_ct_vend = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(ct_vendedores),x='count' , y= vendedores[['count']].sort_values('count', ascending=False).head(ct_vendedores).index,text_auto=True, title= f'Top {ct_vendedores} vendedores (Cantidad de ventas)')
    st.plotly_chart(fig_ct_vend)

#st.dataframe(datos)
