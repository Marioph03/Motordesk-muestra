export interface RegistroJornada {
  id?: number | null;
  usuario_id: number;
  nombre: string;
  apellidos: string;
  fecha: string;
  presente: boolean;
  hora_entrada: string | null;
  hora_salida: string | null;
  hora_entrada_predeterminada: string;
  hora_salida_predeterminada: string;
}
