export interface Damage {

  scratch?: boolean;
  dent?: boolean;
  broken?: boolean;
  replace?: boolean;

}

export interface VehicleDamage {

  [piece: string]: Damage;

}
/** Inspección estructurada de daños visuales capturada desde el diagrama del vehículo. */
