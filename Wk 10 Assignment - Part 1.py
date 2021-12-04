#!/usr/bin/env python
# coding: utf-8

# In[1]:


from copy import deepcopy
import datetime as dt
from IPython.display import HTML
import json
import pandas as pd
from arcgis.gis import GIS
import arcgis.network as network
import arcgis.geocoding as geocoding
from arcgis.features import FeatureLayer, FeatureSet, FeatureCollection
import arcgis.features.use_proximity as use_proximity


# In[2]:


gis = GIS()


# In[4]:


sample_cities = gis.content.search('title:"USA Major Cities" type:Feature Service owner:esri*', 
                                      outside_org=True)[0]
sample_cities


# In[5]:


stops_cities = ['San Francisco', 'San Jose', 'Los Angeles', 'San Diego',
                'Phoenix', 'El Paso', 
                'Houston', 'New Orleans', 'Orlando', 'Miami', 'Dallas']
values = "'" + "', '".join(stops_cities) + "'"


# In[6]:


stops_cities_fl = FeatureLayer(sample_cities.url + "/0")
type(stops_cities_fl)


# In[7]:


stops_cities_fset = stops_cities_fl.query(where="ST in ('CA', 'NV', 'TX', 'AZ', 'LA', 'FL', 'TX')  AND NAME IN ({0})".format(values), as_df=False)
stops_cities_fset


# In[8]:


start_cities_fset = stops_cities_fl.query(where="ST='TX' AND NAME = 'Dallas'", as_df=False)
start_cities_fset


# In[9]:


print(list(map(lambda x: x.attributes['NAME'], stops_cities_fset)))


# In[10]:


def re_order_stop_cities(fset=stops_cities_fset, start_city = "Miami", end_city = "San Francisco"):
    
    stops_cities_flist = []
    last_city = None

    for ea in fset:
        if ea.attributes['NAME'] == start_city:
            stops_cities_flist.insert(0, ea)
        elif ea.attributes['NAME'] == end_city:
            last_city = ea
        else:
            stops_cities_flist.append(ea)
    stops_cities_flist.append(last_city)
 
    return FeatureSet(stops_cities_flist)


# In[11]:


re_ordered_stops_cities_fset = re_order_stop_cities()
re_ordered_stops_cities_fset


# In[12]:


re_ordered_stops_cities_fset.spatial_reference = stops_cities_fset.spatial_reference


# In[13]:


re_ordered_stops_cities = list(map(lambda x: x.attributes['NAME'], re_ordered_stops_cities_fset))
print(re_ordered_stops_cities)


# In[14]:


get_ipython().run_cell_magic('time', '', '\nstart_time = int(dt.datetime.now().timestamp() * 1000)\n\nresult = network.analysis.find_routes(re_ordered_stops_cities_fset, time_of_day=start_time, \n                                      time_zone_for_time_of_day="UTC",\n                                      preserve_terminal_stops="Preserve None",\n                                      reorder_stops_to_find_optimal_routes=True,\n                                      save_output_na_layer=True)')


# In[15]:


print("Is the tool executed successfully?", result.solve_succeeded)


# In[16]:


type(result)


# In[17]:


result.output_routes, result.output_stops, result.output_directions


# In[18]:


start_time = int(dt.datetime.now().timestamp() * 1000)

result = network.analysis.find_routes(re_ordered_stops_cities_fset, time_of_day=start_time, 
                                      time_zone_for_time_of_day="UTC",
                                      preserve_terminal_stops="Preserve None",
                                      reorder_stops_to_find_optimal_routes=True,
                                      save_output_na_layer=True)


# In[19]:


result = network.analysis.find_routes(re_ordered_stops_cities_fset, time_of_day=start_time, 
                                      time_zone_for_time_of_day="UTC",
                                      preserve_terminal_stops="Preserve None",
                                      reorder_stops_to_find_optimal_routes=True,
                                      save_output_na_layer=True)


# In[20]:


result.output_routes, result.output_stops, result.output_directions


# In[21]:


result.output_network_analysis_layer.url


# In[22]:


df = result.output_directions.sdf
df = df[["RouteName", "ArriveTime", "DriveDistance", "ElapsedTime", "Text"]].loc[df["RouteName"] == "Miami - San Francisco"]
df.head()


# In[23]:


df.tail()


# In[24]:


styles = [    
    dict(selector="td", props=[("padding", "2px")]),
    dict(selector='.row_heading, .blank', props=[('display', 'none;')]),
    dict(selector='.col_heading, .blank', props=[('display', 'none;')])]

route_symbol = {
                    "type": "esriSLS",
                    "style": "esriSLSSolid",
                    "color": [128,0,128,90],
                    "width": 4
                }

stops_symbol = {"angle":0,"xoffset":2,"yoffset":8,"type":"esriPMS",
                "url":"http://static.arcgis.com/images/Symbols/Basic/ShinyPin.png",
                "contentType":"image/png","width":24,"height":24}

start_symbol = {"angle":0,"xoffset":0,"yoffset":8.15625,"type":"esriPMS",
                "url":"http://static.arcgis.com/images/Symbols/AtoZ/redA.png",
                "contentType":"image/png","width":15.75,"height":21.75}

end_symbol = {"angle":0,"xoffset":0,"yoffset":8.15625,"type":"esriPMS",
              "url":"http://static.arcgis.com/images/Symbols/AtoZ/greenB.png",
              "contentType":"image/png","width":15.75,"height":21.75}

popup_route = {"title": "Route", 
               "content": df.style.set_table_styles(styles).render()}
popup_stop = {"title": "Stop {}", 
              "content": df.style.set_table_styles(styles).render()}


# In[25]:


def check_curb_approach2(result):
    attributes = result.attributes
    return (attributes['ArriveCurbApproach'], attributes['DepartCurbApproach'])


# In[26]:


map1 = gis.map('Texas, USA', zoomlevel=4)
map1


# In[42]:


for route in result.output_routes:
    map1.draw(route.geometry, popup_route, route_symbol)

sequence = 1
for stop in result.output_stops:
    
    stop_bool_tuple = check_curb_approach2(stop)
    if stop_bool_tuple[0] is None:
      
        symbol = start_symbol
    elif stop_bool_tuple[1] is None:
       
        symbol = end_symbol
    else:
        
        symbol = stops_symbol
        
    address = geocoding.reverse_geocode(stop.geometry)['address']['Match_addr']
    map1.draw(stop.geometry, 
              {"title": "Stop {}".format(sequence), 
               "content": address},
              symbol)
    sequence+=1


# In[28]:


item_properties = {
    "title": "Miami - San Francisco (2)",
    "tags" : "Routing",
    "snippet": " Route from Miami to San Francisco",
    "description": "a web map of Route from Miami to San Francisco using network.RouteLayer.solve"
}

item = map1.save(item_properties)


# In[29]:


item


# In[30]:


re_ordered_values = "'" + "', '".join(re_ordered_stops_cities) + "'"
re_ordered_values


# In[31]:


stops_layer = {'url': sample_cities.layers[0].url, 
               'filter': "ST in ('CA', 'NV', 'TX', 'AZ', 'LA', 'FL')  AND NAME IN ({0})".format(re_ordered_values)}
start_layer = {'url': sample_cities.layers[0].url, 
               'filter': "ST = 'FL' AND NAME = 'Miami'"}
end_layer = {'url': sample_cities.layers[0].url, 
             'filter': "NAME = 'San Francisco'"}


# In[33]:


get_ipython().run_cell_magic('time', '', '\n""" using https://analysis7.arcgis.com/arcgis/rest/services/tasks/GPServer/PlanRoutes/submitJob\n"""\nresult1 = use_proximity.plan_routes(stops_layer=stops_layer, route_count=1, \n                                    max_stops_per_route=10, route_start_time=start_time,\n                                    start_layer_route_id_field = "FID",\n                                    start_layer=start_layer, \n                                    end_layer=end_layer,\n                                    return_to_start=False,\n                                    context={\'outSR\': {"wkid": 4326}},\n                                    output_name="Plan Route from Miami to San Francisco 2a",\n                                    gis=gis)')


# In[35]:


get_ipython().run_cell_magic('time', '', 'result1 = use_proximity.plan_routes(stops_layer=stops_layer, route_count=1, \n                                    max_stops_per_route=10, route_start_time=start_time,\n                                    start_layer_route_id_field = "FID",\n                                    start_layer=start_layer, \n                                    end_layer=end_layer,\n                                    return_to_start=False,\n                                    context={\'outSR\': {"wkid": 4326}},\n                                    output_name="Plan Route from Miami to San Francisco 2a",\n                                    gis=gis)')


# In[36]:


result1


# In[37]:


route_sublayer = FeatureLayer.fromitem(result1, layer_id=1)
route_sublayer.url


# In[38]:


route_sublayer.query(where='1=1', as_df=True)


# In[39]:


map2a = gis.map('Texas, USA', zoomlevel=4)
map2a


# In[40]:


map2a.add_layer(result1)


# In[41]:


get_ipython().run_cell_magic('time', '', '\n""" using https://analysis7.arcgis.com/arcgis/rest/services/tasks/GPServer/PlanRoutes/submitJob\n"""\nresult1 = use_proximity.plan_routes(stops_layer=stops_layer, route_count=1, \n                                   max_stops_per_route=10, route_start_time=start_time,\n                                   start_layer_route_id_field = "FID",\n                                   start_layer=start_layer, \n                                   end_layer=end_layer,\n                                   return_to_start=False,\n                                   context={\'outSR\': {"wkid": 4326}},\n                                   gis=gis)')


# In[43]:


from arcgis.gis import GIS
import arcgis.network as network
from arcgis.features import FeatureLayer, Feature, FeatureSet, use_proximity
import pandas as pd
import datetime as dt
import time


# In[44]:


gis = GIS()


# In[46]:


try:
    hospital_item = gis.content.get("a2817bf9632a43f5ad1c6b0c153b0fab")
except RuntimeError as ne:
    try:
        print("Trying from an alternative source...")
        hospital_item = my_gis.content.get("50fb63f303304835a048d16bd86c3024")
    except RuntimeError as ne:
        print("Trying to publish from csv...")
        import requests
        import csv
        import os

        out_file_name = 'hospitals_SB_county.csv'
        url = "https://data.chhs.ca.gov/datastore/dump/641c5557-7d65-4379-8fea-6b7dedbda40b?q=&sort=_id+asc&fields=OSHPD_ID%2CFACILITY_NAME%2CLICENSE_NUM%2CFACILITY_LEVEL_DESC%2CDBA_ADDRESS1%2CDBA_CITY%2CDBA_ZIP_CODE%2CCOUNTY_CODE%2CCOUNTY_NAME%2CER_SERVICE_LEVEL_DESC%2CTOTAL_NUMBER_BEDS%2CFACILITY_STATUS_DESC%2CFACILITY_STATUS_DATE%2CLICENSE_TYPE_DESC%2CLICENSE_CATEGORY_DESC%2CLATITUDE%2CLONGITUDE&filters=%7B%22COUNTY_CODE%22%3A+%5B%2236%22%5D%7D&format=csv"
        download = requests.get(url)

        with open(out_file_name, 'w') as out_file:
            out_file.writelines(download.text)
            print(out_file_name)
        csv_item = my_gis.content.add({}, out_file_name)
        hospital_item = csv_item.publish()
display(hospital_item)


# In[47]:


hospital_item = gis.content.get("a2817bf9632a43f5ad1c6b0c153b0fab")


# In[48]:


gis = GIS()


# In[49]:


import networkx as nx
import osmnx as ox

get_ipython().run_line_magic('matplotlib', 'inline')
ox.__version__


# In[50]:


conda config --prepend channels conda-forge
conda create -n ox --strict-channel-priority osmnx


# In[51]:


conda config --prepend channels conda-forge


# In[52]:


conda create -n ox --strict-channel-priority osmnx


# In[1]:


import numpy as np
import osmnx as ox

get_ipython().run_line_magic('matplotlib', 'inline')
np.random.seed(0)
ox.__version__


# In[2]:


conda config --prepend channels conda-forge
conda create -n ox --strict-channel-priority osmnx jupyterlab
conda activate ox
python -m ipykernel install --user --name ox --display-name "Python (ox)"
jupyter lab


# In[3]:


import osmnx as ox
get_ipython().run_line_magic('matplotlib', 'inline')
G = ox.graph_from_place('Piedmont, California, USA', network_type='drive')
fig, ax = ox.plot_graph(ox.project_graph(G))


# In[4]:


conda update -n base conda
conda config --prepend channels conda-forge


# In[5]:


import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


# In[6]:


G = nx.barabasi_albert_graph(100,2)


# In[7]:


nx.draw_spring(G);


# In[8]:


G = nx.barabasi_albert_graph(100,2)
nx.draw_spring(G);
plt.hist([v for k,v in nx.degree(G)]);
plt.hist(nx.centrality.closeness_centrality(G).values());
nx.diameter(G)
nx.cluster.average_clustering(G)


# In[9]:


nodes = list(range(100))


# In[10]:


nodes = list(range(100))

df = pd.DataFrame({'from': np.random.choice(nodes, 100),
                   'to': np.random.choice(nodes,100)
                  })


# In[11]:


df


# In[12]:


G = nx.from_pandas_edgelist(df, source='from', target='to')


# In[13]:


nx.draw(G);


# In[14]:


plt.hist([v for k,v in nx.degree(G)]);


# In[ ]:




