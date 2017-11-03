create table DataTypes
(
    DataTypesID text,
    Name text,
    Description text,
    Units text
);
create unique index DT_PK on DataTypes(DataTypesID);

create table DataSources
(
    DataSourceID text,
    Name text,
    Description text
);
create unique index DS_PK on DataSources(DataSourceID);

create table Data
(
    DataTypeID text,
    DataSourceID text,
    ObsTime text,
    value numeric,
    FOREIGN KEY(DataTypeID) REFERENCES DataTypes(DataTypeID),
    FOREIGN KEY(DataSourceID) REFERENCES DataSources(DataSourceID)
);
create unique index D_PK on Data(DataTypeID, DataSourceID, ObsTime);
