export interface Cliente {

    id: number;

    codigo?: string;

    nombre: string;

    apellidos: string;

    dni: string;

    telefono: string;

    email: string;

    direccion: string;

    codigo_postal: string;

    ciudad: string;

    provincia: string;

    observaciones: string;

    activo: boolean;

}
/** Cliente completo presentado por las vistas de gestión del taller. */
