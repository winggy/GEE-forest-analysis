
import ee
ee.Initialize()
    
#forest status
NDVI="MODIS/MOD13A1"
FPAR="MODIS/006/MCD15A3H"
FIRE="MODIS/006/MYD14A2"
EVI="MODIS/MCD43A4_006_EVI"#到2018年
#climate status
LST="MODIS/MYD11A2"
ET="MODIS/NTSG/MOD16A2/105"
RAIN1="JAXA/GPM_L3/GSMaP/v6/reanalysis"
RAIN2="JAXA/GPM_L3/GSMaP/v6/operational"
GLDAS="NASA/GLDAS/V021/NOAH/G025/T3H"
#general status
TCF="MODIS/051/MOD44B"
CATEGOREY="ESA/GLOBCOVER_L4_200901_200912_V2_3"
LANDCOVER="MODIS/051/MCD12Q1"#目前只到2012年
CANOPY_H="NASA/JPL/global_forest_canopy_height_2005"
DEM="USGS/GTOPO30"
#productivity
NPP="MODIS/006/MOD17A3H"#NASA version
GPP="MODIS/055/MOD17A3"#improved version (removed cloud-contaminated pixels )Jan 1, 2000 - Jan 1, 2015

#obtain GEE parameters
col_NDVI = ee.ImageCollection(NDVI).select(tuple({"NDVI"}))
col_EVI = ee.ImageCollection(EVI).select(tuple({"EVI"}))
col_FPAR = ee.ImageCollection(FPAR).select(tuple({"Fpar"}))
col_FIRE = ee.ImageCollection(FIRE).select(tuple({"FireMask"}))

col_LST_Day  = ee.ImageCollection(LST).select(tuple({"LST_Day_1km"}))
col_LST_Night  = ee.ImageCollection(LST).select(tuple({"LST_Night_1km"}))
col_ET = ee.ImageCollection(ET).select(tuple({"ET"}))
col_RAIN = ee.ImageCollection([RAIN1,RAIN2]).select(tuple({"hourlyPrecipRate"}))
col_Canopywater=ee.ImageCollection(GLDAS).select(tuple({"CanopInt_inst"}))
col_Rootmoist=ee.ImageCollection(GLDAS).select(tuple({"RootMoist_inst"}))

col_TCF = ee.ImageCollection(TCF).select(tuple({"Percent_Tree_Cover"}))

img_landtype=ee.Image(CATEGOREY).select('landcover')
img_CANOPY_H=ee.Image(CANOPY_H).select('1')
img_DEM=ee.Image(DEM).select('elevation')

col_NPP=ee.ImageCollection(GPP).select(tuple({"Npp"}))#use the improved version
col_GPP=ee.ImageCollection(GPP).select(tuple({"Gpp"}))

#%%
#import the  geographic coordinate centers of forest points
import pandas as pd
import numpy as np
samples=pd.read_csv("forest_samples_new.csv")
samples.sort_values(by=['longitude','latitude'])
PX=list(samples.longitude)
PY=list(samples.latitude)
geolen=1 
geolist=[]
for j in range(int(len(PX)/geolen)):
    ListP= []
    for i in range(j*geolen,j*geolen+geolen): 
        ListP.append(PX[i])
        ListP.append(PY[i])
    Pgeometry = ee.Geometry.MultiPoint(ListP)
    geolist.append(Pgeometry)

#%%
import csv
def Obtain_monthly_data(yearlist,product,pointlist,filename,func,scale): 
    # func=0 - ave; func=1 - sum 
    mlist=['01','02','03','04','05','06','07','08','09','10','11','12']
    Month=list(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
    D=list(['31','28','31','30','31','30','31','31','30','31','30','31'])
    parnum=len(yearlist)*12
    datelist=[]
    headlist=[]
    headlist.append('longitude')
    headlist.append('latitude')
    for year in yearlist:
        for m in Month:
            datelist.append(str(str(year)+'-'+m))
            headlist.append(str(str(year)+'-'+m))
    #写CSV文件头
#     if (filename is not None):
#         f=open(filename,'wb')
#         writer=csv.writer(f)
#         writer.writerow(headlist)
#         f.close()
    count=0        
    product=ee.ImageCollection(product)
    parDF=pd.DataFrame()
    for geo in pointlist:
        Pgeometry=geo
        Ilist=[]
        for year in yearlist:
            for m in range(0,len(mlist)):
                if (func==0) :
                  I0=product.filterDate(str(year)+'-'+mlist[m]+'-01',str(year)+'-'+mlist[m]+'-'+D[m]).mean()
                else:
                  I0=product.filterDate(str(year)+'-'+mlist[m]+'-01',str(year)+'-'+mlist[m]+'-'+D[m]).sum()
                Ilist.append(I0)
        I=ee.ImageCollection.fromImages(Ilist)
        region =I.getRegion(Pgeometry, scale).getInfo()
        df = pd.DataFrame.from_records(region[1:len(region)])
        df.columns = region[0]
        Tdf=df.iloc[:,4].values.reshape(df.shape[0]/parnum,parnum)
        Tf=pd.DataFrame()
        Tf['longitude']=df['longitude'][::parnum]
        Tf['latitude']=df['latitude'][::parnum]
        for i in range(0,parnum):
          Tf[datelist[i]]=Tdf[:,i]

        parDF=pd.concat([parDF,Tf])

        count+=Tf.shape[0]
        if count%50==0:print(count)
    
    if(filename is not None):
        parDF.to_csv(filename, index = False, columns=parDF.columns)    
    print('done')
    return parDF          
          


# In[ ]:

def Obtain_yearly_data(yearlist,product,pointlist,filename,scale): 
    # 获取年数据
    parnum=len(yearlist)*1
    datelist=[]
    product=ee.ImageCollection(product)

    parDF=pd.DataFrame()
    for geo in pointlist:
        Pgeometry=geo
        Ilist=[]
        for year in yearlist:
            print(year)          
            I0=product.filterDate(str(year)+'-01-01',str(year)+'-12-31')
            Ilist.append(I0)
        I=ee.ImageCollection(Ilist)
        region =I.getRegion(Pgeometry, scale).getInfo()
        df = pd.DataFrame.from_records(region[1:len(region)])
        df.columns = region[0]
        Tdf=df.iloc[:,4].values.reshape(df.shape[0]/parnum,parnum)
        Tf=pd.DataFrame()
        Tf['longitude']=df['longitude'][::parnum]
        Tf['latitude']=df['latitude'][::parnum]
        for i in range(0,parnum):
          Tf[yearlist[i]]=Tdf[:,i]

        pd.concat([parDF,Tf])
    if (filename is not None):
        parDF.to_csv(filename, index = False, columns=parDF.columns)
    print('done')
    return parDF          
          


# In[6]:

def Obtain_aux_data(product,pointlist,filename,scale): 
    # 获取非时序属性数据
    parDF=pd.DataFrame()
    for geo in pointlist:
        Pgeometry=geo
        I=ee.ImageCollection([product])
        region =I.getRegion(Pgeometry, scale).getInfo()
        df = pd.DataFrame.from_records(region[1:len(region)])
        df.columns = region[0]
        Tdf=df.iloc[:,4].values.reshape(df.shape[0]/parnum,parnum)
        Tf=pd.DataFrame()
        Tf['longitude']=df['longitude'][::parnum]
        Tf['latitude']=df['latitude'][::parnum]
        for i in range(0,parnum):
          Tf[yearlist[i]]=Tdf[:,i]

        pd.concat([parDF,Tf])
    if (filename is not None):
        parDF.to_csv(filename, index = False, columns=parDF.columns)
    print('done')
    return parDF  


# In[4]:

#月均值数据列表
listP1=list([col_NDVI,col_EVI,col_ET,col_LST_Day,col_LST_Night])
listP1name=list(['NDVI','EVI','ET','LSTD','LSTN'])
#月累计数据列表
listP2=list([col_RAIN,col_Canopywater,col_Rootmoist])
listP2name=list(['RAIN','canopywater','rootmoist'])
#年数据列表
listP3=list([col_TCF,col_GPP,col_NPP])
listP3name=list(['TCF','GPP','NPP'])
#属性数据列表
listP4=list([img_DEM,img_landtype])
listP4=list(['DEM','Landtype'])


# In[ ]:

yearlist=range(2004,2014)

for i in range(0,len(listP1)):
    p=listP1[i]
    filename=listP1name[i]+'2004-2013.csv'
    print(listP1name[i])
    Obtain_monthly_data(yearlist,p,geolist,filename,0,10000)

for i in range(0,len(listP2)):
    p=listP2[i]
    filename=listP2name[i]+'2004-2013.csv'
    print(listP2name[i])
    Obtain_monthly_data(yearlist,p,geolist,filename,1,10000)

for i in range(0,len(listP3)):
    p=listP3[i]
    filename=listP3name[i]+'2004-2013.csv'     
    print(listP3name[i])
    Obtain_yearly_data(yearlist,p,geolist,filename,10000)

for i in range(0,len(listP4)):
    p=listP4[i]
    filename=listP4name[i]+'.csv'
    print(listP4name[i])
    Obtain_aux_data(p,geolist,filename,10000)



    

