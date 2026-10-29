export interface SeguridadUsuario {
  id: number;
  nombre: string;
  email: string;
  rol: string;
  ultimo_acceso?: string | null;
}

export interface CambiarPasswordRequest {
  password_actual: string;
  password_nueva: string;
}
/** Datos de seguridad de perfil requeridos por la pantalla de credenciales. */
