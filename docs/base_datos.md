Cliente

Campos:

id
nombre
apellidos
dni
telefono
email
direccion
ciudad
codigo_postal
notas
fecha_creacion

Vehículo:

id
cliente_id
matrícula
VIN
marca
modelo
año
combustible
kilómetros
color
observaciones

Reparación:

id
vehiculo_id
estado
descripción
fecha entrada
fecha salida
empleado
coste mano de obra

Factura:

id
reparación
fecha
IVA
subtotal
total

Líneas de factura:

descripción
cantidad
precio
IVA