import { UsuarioActual } from './usuario-actual';

export interface TokenResponse {

  access_token: string;

  token_type: string;

  usuario: UsuarioActual;

}
/** Forma mínima de la respuesta JWT que persiste temporalmente el cliente. */
