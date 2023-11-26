-- Crear la base de datos
CREATE DATABASE IF NOT EXISTS db_vascus;

-- Seleccionar la base de datos
USE db_vascus;

-- Crear la tabla Clientes
CREATE TABLE IF NOT EXISTS Clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Nombre VARCHAR(255) NOT NULL,
    Celular VARCHAR(15),
    Tipo_Documento VARCHAR(20),
    Num_Documento VARCHAR(20),
    Ciudad VARCHAR(50),
    Direccion VARCHAR(255),
    Tipo_Cliente VARCHAR(50)
);

-- Crear la tabla Insumos
CREATE TABLE IF NOT EXISTS Insumos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Nombre VARCHAR(255) NOT NULL,
    Fecha_Compra DATE,
    Fecha_Vencimiento DATE,
    Dias_Caducar INT,
    Precio_Total DOUBLE,
    Cantidad_Adquirida DOUBLE,
    Cantidad_Disponible DOUBLE,
    Cantidad_Usada DOUBLE,
    Unidad_Medida VARCHAR(50),
    Desperdicio INT,
    Proveedor VARCHAR(255),
    Precio_Unitario DOUBLE
);

-- Crear la tabla Productos
CREATE TABLE IF NOT EXISTS Productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Nombre_Producto VARCHAR(255) NOT NULL,
    Cantidad_Insumo DOUBLE
);

-- Crear la tabla intermedia ProductosInsumos
CREATE TABLE IF NOT EXISTS ProductosInsumos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_Producto INT,
    id_Insumo INT,
    FOREIGN KEY (id_Producto) REFERENCES Productos(id),
    FOREIGN KEY (id_Insumo) REFERENCES Insumos(id)
);

-- Crear la tabla Lotes
CREATE TABLE IF NOT EXISTS Lotes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Fecha_Fabricacion DATE,
    Fecha_Vencimiento DATE,
    Dias_Caducar INT,
    Unidades_Preparadas DOUBLE,
    Costo_Unitario DOUBLE,
    Precio_Detal DOUBLE,
    Precio_Mayorista DOUBLE,
    Unidades_Totales_vendidas DOUBLE,
    Ventas_Totales DOUBLE,
    Unidades_Disponibles DOUBLE,
    Utilidad_Total DOUBLE
);

-- Crear la tabla intermedia ProductosLotes
CREATE TABLE IF NOT EXISTS ProductosLotes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_Producto INT,
    id_Lote INT,
    FOREIGN KEY (id_Producto) REFERENCES Productos(id),
    FOREIGN KEY (id_Lote) REFERENCES Lotes(id)
);

-- Crear la tabla Ventas
CREATE TABLE IF NOT EXISTS Ventas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Nombre_Vendedor VARCHAR(255),
    Tipo_Venta VARCHAR(50),
    Precio_Lote DOUBLE,
    Unidades_Vendidas_Producto INT,
    Subtotal_Producto DOUBLE,
    Subtotal_Venta DOUBLE,
    Fecha_venta DATE,
    Descuento INT,
    Costo_Envio DOUBLE,
    Total_Venta DOUBLE
);

-- Crear la tabla intermedia VentasLotes
CREATE TABLE IF NOT EXISTS VentasLotes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_Venta INT,
    id_Lote INT,
    FOREIGN KEY (id_Venta) REFERENCES Ventas(id),
    FOREIGN KEY (id_Lote) REFERENCES Lotes(id)
);

-- Crear la tabla intermedia VentasProductos
CREATE TABLE IF NOT EXISTS VentasProductos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_Venta INT,
    id_Producto INT,
    FOREIGN KEY (id_Venta) REFERENCES Ventas(id),
    FOREIGN KEY (id_Producto) REFERENCES Productos(id)
);

-- Crear la tabla intermedia VentasClientes
CREATE TABLE IF NOT EXISTS VentasClientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_Venta INT,
    id_Cliente INT,
    FOREIGN KEY (id_Venta) REFERENCES Ventas(id),
    FOREIGN KEY (id_Cliente) REFERENCES Clientes(id)
);

