import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable, Service } from '@angular/core';
import { API_URL } from '../../../core/tokens/api.token';
import { Observable } from 'rxjs';

import { Vehiculo } from '../models/vehiculo';
import { VehiculoCreate } from '../models/vehiculo-create';
import { VehiculoPage } from '../models/vehiculo-page';
import { VehiculoSelect } from '../models/vehiculo-select';

@Injectable({
providedIn: 'root'
})
export class Vehiculos {

  private http = inject(HttpClient);

  private apiUrl = inject(API_URL);

  getVehiculos(
  page: number = 1,
  size: number = 10,
  q: string = ''
): Observable<VehiculoPage> {

  let params = new HttpParams()
    .set('page', Math.max(1, page))
    .set('size', size);

  if (q.trim()) {
    params = params.set('q', q.trim());
  }

  return this.http.get<VehiculoPage>(
    `${this.apiUrl}/vehiculos/`,
    {
      params
    }
  );

}

  getVehiculo(id: number): Observable<Vehiculo> {

  return this.http.get<Vehiculo>(
    `${this.apiUrl}/vehiculos/${id}`
  );

}

  createVehiculo(
  vehiculo: VehiculoCreate
  ) {
  return this.http.post(
    `${this.apiUrl}/vehiculos/`,
    vehiculo
  );
}

  updateVehiculo(
  id: number,
  vehiculo: VehiculoCreate
  ) {
  return this.http.put(
    `${this.apiUrl}/vehiculos/${id}`,
    vehiculo
  );
}

  deleteVehiculo(id: number) {
  return this.http.delete(
    `${this.apiUrl}/vehiculos/${id}`
  );
}

getVehiculosSelect(): Observable<VehiculoSelect[]> {
  return this.http.get<VehiculoSelect[]>(
    `${this.apiUrl}/vehiculos/select`
  );
}

}
/** Cliente HTTP del parque de vehículos y sus operaciones CRUD. */
