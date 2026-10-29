import {
  AfterViewInit,
  Component,
  ViewChild,
  input,
  signal
} from '@angular/core';
import { MatCardModule } from '@angular/material/card';

import { Orden } from './../../models/orden';
import {
  VehicleDiagram3D,
  VehicleDamage
} from './components/vehicle-diagram-3d/vehicle-diagram-3d';

@Component({
  selector: 'app-estado-vehiculo',
  standalone: true,
  imports: [
    MatCardModule,
    VehicleDiagram3D
  ],
  templateUrl: './estado-vehiculo.html',
  styleUrl: './estado-vehiculo.scss'
})
export class EstadoVehiculo implements AfterViewInit {

  readonly orden_input = input.required<Orden>();

  readonly mostrarVisor = signal(false);

  @ViewChild(VehicleDiagram3D)
  private visor!: VehicleDiagram3D;

  ngAfterViewInit(): void {

    requestAnimationFrame(() => {

      this.mostrarVisor.set(true);

      requestAnimationFrame(() => {

        this.visor?.setDamages(
          this.orden_input().vehicle_damage ?? {}
        );

      });

    });

  }

  getDamageState(): VehicleDamage {

    return this.visor?.getDamages() ?? {};

  }

}
/** Resumen visual de la inspección y estado del vehículo vinculado a una orden. */
