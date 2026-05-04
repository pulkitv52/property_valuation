# Phase 1 Data Understanding Report

This report summarizes the transaction and GIS datasets required for Use Case 1.

## transactions

- Type: tabular
- Rows: 344079
- Columns: 56
- Duplicate rows: 40653
- Candidate join keys: Deed_No, Deed_Year, Registration_district_code, Registration_district_Name, Registration_RO_code, Registration_Office_Name, Transaction_code, Transaction_Name, sl_no_Property, property_district_code, property_district_Name, Property_Office_code, property_Office_Name, ps_code, PS_Name, mouza_code, Mouza_Name, plot_code_type, plot_no, bata_plot_no, premises, Road_code, Road_Name, Zone_no, Special_project_Name, Is_Property_on_Road, Approach_Road_Width, Adjacent_to_Metal_Road, Proposed_Land_use_Code, Proposed_Land_use_Name, Nature_Land_use_Code, Nature_Land_use_Name, Proposed_Apartment_use_Name, Nature_Apartment_use_name, Litigated_Property, Mouza_Type, Road_Category

### Top Missing Columns

- Road_Category: 344079 missing (100.0%)
- premises: 341027 missing (99.11%)
- Road_Name: 253403 missing (73.65%)
- Proposed_Apartment_use_Name: 183168 missing (53.23%)
- Nature_Apartment_use_name: 183168 missing (53.23%)
- Nature_Land_use_Name: 160911 missing (46.77%)
- bargadar: 160911 missing (46.77%)
- Proposed_Land_use_Name: 160911 missing (46.77%)
- is_bargadar_purchaser: 160911 missing (46.77%)
- whether_tenant_purchaser: 160911 missing (46.77%)
- Special_project_Name: 1929 missing (0.56%)
- Approach_Road_Width: 65 missing (0.02%)
- market_value: 37 missing (0.01%)
- Road_code: 9 missing (0.0%)

### Outlier Summary

- market_value: 11123 outliers, bounds=(-2590800.0, 4810480.0)
- setforth_value: 16763 outliers, bounds=(-1844647.5, 3178788.5)
- Area: 7022 outliers, bounds=(-787.5375, 1316.7545)

### Schema

- query_year: int64
- query_no: int64
- book: object
- Deed_No: int64
- Deed_Year: int64
- Registration_district_code: int64
- Registration_district_Name: object
- Registration_RO_code: int64
- Registration_Office_Name: object
- Transaction_code: int64
- Transaction_Name: object
- Date_of_presentation: object
- Date_of_Registration: object
- Time_of_Presentation: object
- sl_no_Property: int64
- property_district_code: int64
- property_district_Name: object
- Property_Office_code: int64
- property_Office_Name: object
- ps_code: int64
- PS_Name: object
- mouza_code: int64
- Mouza_Name: object
- plot_code_type: object
- plot_no: int64
- bata_plot_no: int64
- premises: object
- Urban: object
- Rural: object
- Road_code: object
- Road_Name: object
- Zone_no: int64
- Special_project_Name: object
- Is_Property_on_Road: object
- Approach_Road_Width: float64
- Adjacent_to_Metal_Road: object
- Proposed_Land_use_Code: object
- Proposed_Land_use_Name: object
- Nature_Land_use_Code: object
- Nature_Land_use_Name: object
- Proposed_Apartment_use_Name: object
- Nature_Apartment_use_name: object
- Litigated_Property: object
- bargadar: object
- whether_tenant_purchaser: object
- Area_type: object
- Area: float64
- Types of area Measurement: object
- Sq ft: float64
- Market value per sq ft: float64
- setforth_value: int64
- market_value: float64
- is_bargadar_purchaser: object
- Mouza_Type: object
- Road_Category: float64
- Flat_or_Land: object

## property_layer

- Type: geospatial
- Rows: 111497
- Columns: 29
- Duplicate rows: 0
- Candidate join keys: BLOCK_CODE, PS_CODE, ps_name, moucode, mouza_type, Dist_name, plot_no, dist_code
- CRS: EPSG:4326
- Geometry types: {"Polygon": 111255, "MultiPolygon": 242}
- Invalid geometries: 27
- Bounds: {"minx": 87.31461443900008, "miny": 22.524414345000025, "maxx": 88.23524627300009, "maxy": 23.54926189300005}

### Top Missing Columns

- Municipali: 60874 missing (54.6%)
- Ward_No: 55597 missing (49.86%)
- sabek_pt2: 53926 missing (48.37%)
- GP: 50644 missing (45.42%)
- SHEET_NO: 50644 missing (45.42%)
- idn: 50623 missing (45.4%)
- bata_no: 14409 missing (12.92%)
- sabek_pt1: 12608 missing (11.31%)
- hal_pt2: 7107 missing (6.37%)
- BLOCK: 4914 missing (4.41%)
- hal_pt1: 4617 missing (4.14%)

### Outlier Summary

- No configured outlier columns available in this dataset

### Schema

- OBJECTID: int64
- BLOCK_CODE: object
- BLOCK: object
- PS_CODE: object
- ps_name: object
- Municipali: object
- ADSR_OFFIC: object
- JL_NO: object
- moucode: object
- idn: object
- ENG_MOUNAM: object
- mouza_type: object
- LR_RS: object
- SHEET_NO: object
- GP: object
- bata_no: object
- hal_pt1: object
- hal_pt2: object
- sabek_pt1: object
- sabek_pt2: object
- CENT_LAT: float64
- CENT_LONG: float64
- Dist_name: object
- Ward_No: object
- SHAPE_Leng: float64
- SHAPE_Area: float64
- plot_no: object
- dist_code: object
- geometry: geometry

## road_layer

- Type: geospatial
- Rows: 10345
- Columns: 10
- Duplicate rows: 0
- Candidate join keys: R_NAME
- CRS: EPSG:32645
- Geometry types: {"LineString": 10298, "MultiLineString": 47}
- Invalid geometries: 0
- Bounds: {"minx": 532147.0055999998, "miny": 2491316.409499999, "maxx": 626955.4446, "maxy": 2604357.956599999}

### Top Missing Columns

- R_NAME: 9872 missing (95.43%)

### Outlier Summary

- No configured outlier columns available in this dataset

### Schema

- OBJECTID_1: int64
- OBJECTID: int64
- R_NAME: object
- R_CATG: object
- R_WIDTH: float64
- R_TOP_MAT: object
- Shape_Leng: float64
- Shape_Le_1: float64
- adsr_jur: object
- geometry: geometry

## facilities_layer

- Type: geospatial
- Rows: 238
- Columns: 21
- Duplicate rows: 0
- Candidate join keys: State_Name, District_N, Office_Nam
- CRS: EPSG:4326
- Geometry types: {"Point": 238}
- Invalid geometries: 0
- Bounds: {"minx": 87.32659000000007, "miny": 22.531858300000067, "maxx": 88.23467680000005, "maxy": 23.54538270000012}

### Top Missing Columns

- Email_Id: 238 missing (100.0%)

### Outlier Summary

- No configured outlier columns available in this dataset

### Schema

- OBJECTID: int64
- Survey_Id: object
- Report_Dat: datetime64[ms]
- State_Name: object
- District_N: object
- Block__ULB: object
- Police_Sta: object
- GP_Ward: object
- Facility_T: object
- Survey_Poi: object
- Brief_Desc: object
- Geo_Latitu: float64
- Geo_Longit: float64
- Geo_Locati: object
- Reporting: float64
- Report_D_1: datetime64[ms]
- Survey_Use: object
- Designatio: object
- Email_Id: object
- Office_Nam: object
- geometry: geometry
