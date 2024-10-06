drop table Users;
drop table Menu;
drop table Kombo;

create TABLE Users(
    id int primary key,
    phone text,
    username text,
    usermail text,
    userpassword text,
    userbonus int
);
create TABLE Menu(
    id int primary key,
    dishtype int,
    dishname text,
    dishdescription text,
    dishcomposition text,
    dishprice float,
    dishoffer int
);
create TABLE Kombo(
    id int primary key,
    komboname text,
    kombodescription text,
    kombocomposition text,
    komboprice float,
    kombooffer int
);

create TABLE Orders(
    id int primary key,
    orderscomposition text,
    orderssum float,
    orderscount int,
    ordersoffer int
)
