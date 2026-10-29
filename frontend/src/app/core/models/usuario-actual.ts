export interface UsuarioActual {
  id: number;
  nombre: string;
  apellidos: string;
  email: string;
  rol: string;
  activo: boolean;
  avatar_url?: string | null;
  permisos: string[];
}
/** Perfil autenticado y permisos usados para adaptar la experiencia visual. */
