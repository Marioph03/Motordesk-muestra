import {
  Component,
  OnInit,
  inject
} from '@angular/core';

import { CommonModule } from '@angular/common';

import {
  FormBuilder,
  ReactiveFormsModule,
  Validators
} from '@angular/forms';

import {
  ActivatedRoute,
  Router
} from '@angular/router';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatIconModule } from '@angular/material/icon';

import { CitasService } from '../../services/citas.service';
import { CitaCreate } from '../../models/cita-create';
import { CitaUpdate } from '../../models/cita-update';
import { Cita } from '../../models/cita';
import { Observable } from 'rxjs';

import { Vehiculos } from '../../../vehiculos/services/vehiculos';
import { VehiculoSelect } from '../../../vehiculos/models/vehiculo-select';
import { AutocompleteSelect } from '../../../../shared/components/autocomplete-select/autocomplete-select';

import {
  NotificationService
} from '../../../../shared/services/notification';
import {
  DisponibilidadUsuario,
  PersonalService
} from '../../../personal/services/personal.service';
import { Personal } from '../../../personal/models/personal';
import { ConfiguracionAgendaService } from '../../../configuracion/services/configuracion-agenda.service';


@Component({
  selector: 'app-cita-form',

  standalone: true,

  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatIconModule,
    AutocompleteSelect
  ],

  templateUrl: './cita-form.html',

  styleUrl: './cita-form.scss'
})
export class CitaForm implements OnInit {

  private fb = inject(FormBuilder);

  private citasService =
    inject(CitasService);

  private vehiculosService =
    inject(Vehiculos);

  private personalService =
    inject(PersonalService);

  private notification =
    inject(NotificationService);

  private configuracionAgendaService =
    inject(ConfiguracionAgendaService);

  private route =
    inject(ActivatedRoute);

  private router =
    inject(Router);


  isEditMode = false;

  citaId?: number;

  cita?: Cita;

  reprogramando = false;

  vehiculos: VehiculoSelect[] = [];

  usuarios: Personal[] = [];

  disponibilidadUsuarios = new Map<
    number,
    DisponibilidadUsuario
  >();

  etiquetaVehiculo = (vehiculo: VehiculoSelect): string =>
    vehiculo.descripcion;

  comprobandoDisponibilidad = false;

  disponible: boolean | null = null;

  duracionPredeterminada = 30;

  form = this.fb.group({

    vehiculo_id: [
      null as number | null,
      Validators.required
    ],

    fecha: [
      '',
      Validators.required
    ],

    hora_inicio: [
      '',
      Validators.required
    ],

    usuarios_ids: [
      [] as number[]
    ],

    motivo: [
      '',
      [
        Validators.required,
        Validators.maxLength(500)
      ]
    ],

    observaciones: ['']

  });


  ngOnInit(): void {

    this.cargarVehiculos();
    this.cargarUsuarios();
    this.cargarConfiguracionAgenda();

    const id =
      this.route.snapshot.paramMap.get('id');

    if (id) {

      this.isEditMode = true;

      this.citaId = Number(id);

      this.cargarCita();

    }

    const fechaParam =
      this.route.snapshot.queryParamMap.get('fecha');

    const horaInicioParam =
      this.route.snapshot.queryParamMap.get('horaInicio');

    if (!this.isEditMode) {
      this.form.patchValue({
        fecha: fechaParam ?? '',
        hora_inicio: horaInicioParam ?? ''
      });
    }



  }

  cargarConfiguracionAgenda(): void {
    this.configuracionAgendaService.getConfiguracion().subscribe({
      next: configuracion => {
        this.duracionPredeterminada = configuracion.duracion_cita_minutos;

        if (this.form.value.fecha && this.form.value.hora_inicio) {
          this.actualizarHoraFin();
        }
      },
      error: err => this.notification.showHttpError(err)
    });
  }


  cargarVehiculos(): void {

    this.vehiculosService
      .getVehiculosSelect()
      .subscribe({

        next: vehiculos => {

          this.vehiculos = vehiculos;

        },

        error: err => {

          this.notification.showHttpError(
            err
          );

        }

      });

  }

  cargarUsuarios(): void {

    this.personalService
      .getPersonal()
      .subscribe({

        next: usuarios => {
          this.usuarios = usuarios.filter(
            usuario => usuario.activo
          );
        },

        error: err => {
          this.notification.showHttpError(err);
        }

      });

  }


  cargarCita(): void {

    if (!this.citaId) {
      return;
    }

    this.citasService
      .getCita(
        this.citaId
      )
      .subscribe({

        next: cita => {

          this.cita = cita;

          const inicio =
            new Date(
              cita.fecha_inicio
            );

          this.form.patchValue({

            vehiculo_id:
              cita.vehiculo_id,

            fecha:
              this.formatearFechaInput(
                inicio
              ),

            hora_inicio:
              this.formatearHoraInput(
                inicio
              ),

            usuarios_ids:
              cita.usuarios_asignados.map(
                usuario => usuario.id
              ),

            motivo:
              cita.motivo,

            observaciones:
              cita.observaciones ?? ''

          });

          this.comprobarDisponibilidadPersonal();

        },

        error: err => {

          this.notification.showHttpError(
            err
          );

          this.router.navigate([
            '/agenda'
          ]);

        }

      });

  }


  guardar(): void {

    if (this.form.invalid) {

      this.form.markAllAsTouched();

      return;

    }

    const fecha =
      this.form.value.fecha!;

    const horaInicio =
      this.form.value.hora_inicio!;

    const fechaInicio =
      `${fecha}T${horaInicio}:00`;

    const fechaFin = this.fechaFinTecnica(fechaInicio);


    const vehiculoId =
      this.form.value.vehiculo_id!;

    const vehiculo =
      this.vehiculos.find(
        item =>
          item.id === vehiculoId
      );

    if (!vehiculo) {

      this.notification.error(
        'Vehículo no encontrado.'
      );

      return;

    }

    /*
     * IMPORTANTE:
     * El backend necesita cliente_id y vehiculo_id.
     *
     * Si VehiculoSelect ya contiene cliente_id,
     * usa vehiculo.cliente_id.
     *
     * Si no lo contiene, lo añadiremos al modelo/select
     * en el siguiente ajuste.
     */

    const clienteId =
      (vehiculo as any).cliente_id;

    if (!clienteId) {

      this.notification.error(
        'No se pudo determinar el cliente del vehículo.'
      );

      return;

    }


    if (this.isEditMode) {

      const datos: CitaUpdate = {

        cliente_id:
          clienteId,

        vehiculo_id:
          vehiculoId,

        usuarios_ids:
          this.form.value.usuarios_ids ?? [],

        fecha_inicio:
          fechaInicio,

        fecha_fin:
          fechaFin,

        motivo:
          this.form.value.motivo!,

        observaciones:
          this.form.value.observaciones ?? ''

      };

      this.citasService
        .actualizarCita(
          this.citaId!,
          datos
        )
        .subscribe({

          next: cita => {

            this.cita = cita;
            this.reprogramando = false;

            this.notification.success(
              cita.fecha_reprogramacion
                ? 'Cita reprogramada correctamente.'
                : 'Cita actualizada correctamente.'
            );

          },

          error: err => {

            this.notification.showHttpError(
              err
            );

          }

        });

      return;

    }


    const datos: CitaCreate = {

      cliente_id:
        clienteId,

      vehiculo_id:
        vehiculoId,

      usuarios_ids:
        this.form.value.usuarios_ids ?? [],

      fecha_inicio:
        fechaInicio,

      fecha_fin:
        fechaFin,

      motivo:
        this.form.value.motivo!,

      observaciones:
        this.form.value.observaciones ?? ''

    };


    this.citasService
      .crearCita(
        datos
      )
      .subscribe({

        next: () => {

          this.notification.success(
            'Cita creada correctamente.'
          );

          this.router.navigate([
            '/agenda'
          ]);

        },

        error: err => {

          this.notification.showHttpError(
            err
          );

        }

      });

  }


  cancelar(): void {

    this.router.navigate([
      '/agenda'
    ]);

  }

  crearOrden(): void {
    if (!this.citaId) return;
    this.citasService.crearOrdenDesdeCita(this.citaId).subscribe({
      next: orden => {
        this.notification.success(`Orden ${orden.numero} creada correctamente.`);
        void this.router.navigate(['/ordenes', orden.id]);
      },
      error: err => this.notification.showHttpError(err)
    });
  }

  crearPresupuesto(): void {
    if (!this.citaId) return;
    this.citasService.crearPresupuestoDesdeCita(this.citaId).subscribe({
      next: presupuesto => {
        this.notification.success(`Presupuesto ${presupuesto.numero} creado correctamente.`);
        void this.router.navigate(['/ordenes', presupuesto.id]);
      },
      error: err => this.notification.showHttpError(err)
    });
  }

  enviarConfirmacionEmail(): void {
    if (!this.citaId) return;
    this.citasService.enviarConfirmacionEmail(this.citaId).subscribe({
      next: cita => {
        this.cita = cita;
        this.notification.success('Confirmación enviada por email correctamente.');
      },
      error: err => this.notification.showHttpError(err)
    });
  }

  iniciarReprogramacion(): void {
    this.reprogramando = true;
  }

  avisarReprogramacionEmail(): void {
    if (!this.citaId) return;

    this.citasService.avisarReprogramacionEmail(this.citaId).subscribe({
      next: () => this.notification.success('Aviso de cambio enviado por email correctamente.'),
      error: err => this.notification.showHttpError(err)
    });
  }

  confirmarCita(): void {
    this.cambiarEstado(
      () => this.citasService.confirmarCita(this.citaId!),
      'Cita confirmada correctamente.'
    );
  }

  marcarEnTaller(): void {
    this.cambiarEstado(
      () => this.citasService.marcarEnTaller(this.citaId!),
      'Cliente marcado como llegado al taller.'
    );
  }

  completarCita(): void {
    this.cambiarEstado(
      () => this.citasService.completarCita(this.citaId!),
      'Cita completada correctamente.'
    );
  }

  cancelarCita(): void {
    this.cambiarEstado(
      () => this.citasService.cancelarCita(this.citaId!),
      'Cita cancelada correctamente.'
    );
  }

  marcarNoPresentado(): void {
    this.cambiarEstado(
      () => this.citasService.marcarNoPresentado(this.citaId!),
      'Cita marcada como no presentada.'
    );
  }

  private cambiarEstado(
    solicitud: () => Observable<Cita>,
    mensaje: string
  ): void {
    if (!this.citaId) {
      return;
    }

    solicitud().subscribe({
      next: cita => {
        this.cita = cita;
        this.notification.success(mensaje);
      },
      error: err => this.notification.showHttpError(err)
    });
  }


  private formatearFechaInput(
    fecha: Date
  ): string {

    const year =
      fecha.getFullYear();

    const month =
      String(
        fecha.getMonth() + 1
      ).padStart(2, '0');

    const day =
      String(
        fecha.getDate()
      ).padStart(2, '0');

    return `${year}-${month}-${day}`;

  }


  private formatearHoraInput(
    fecha: Date
  ): string {

    const hora =
      String(
        fecha.getHours()
      ).padStart(2, '0');

    const minutos =
      String(
        fecha.getMinutes()
      ).padStart(2, '0');

    return `${hora}:${minutos}`;

  }

  comprobarDisponibilidad(): void {
    const fecha = this.form.value.fecha;
    const horaInicio = this.form.value.hora_inicio;

    if (!fecha || !horaInicio) {
      this.disponible = null;
      return;
    }

    const inicio = `${fecha}T${horaInicio}:00`;

    this.comprobandoDisponibilidad = true;
    this.citasService.getCitasPorRango(inicio, this.fechaFinTecnica(inicio)).subscribe({
      next: citas => {
        this.disponible = citas.filter(cita => cita.id !== this.citaId && cita.estado !== 'Cancelada' && cita.estado !== 'No presentado').length === 0;
        this.comprobandoDisponibilidad = false;
      },
      error: err => {
        this.comprobandoDisponibilidad = false;
        this.disponible = null;
        this.notification.showHttpError(err);
      }
    });

    this.comprobarDisponibilidadPersonal();
  }

  actualizarHoraFin(): void {
    if (!this.form.value.fecha || !this.form.value.hora_inicio) {
      this.disponible = null;
      return;
    }

    // La hora final no se muestra al usuario: se usa para reservar la franja
    // configurada y validar solapes/disponibilidad antes de guardar.
    this.comprobarDisponibilidad();
  }

  comprobarDisponibilidadPersonal(): void {
    const fecha = this.form.value.fecha;
    const horaInicio = this.form.value.hora_inicio;

    if (!fecha || !horaInicio) {
      this.disponibilidadUsuarios.clear();
      return;
    }

    const inicio = `${fecha}T${horaInicio}:00`;
    const fin = this.fechaFinTecnica(inicio);

    this.personalService
      .getDisponibilidad(
        inicio,
        fin,
        this.citaId
      )
      .subscribe({
        next: disponibilidad => {
          this.disponibilidadUsuarios = new Map(
            disponibilidad.map(item => [
              item.usuario_id,
              item
            ])
          );
        },
        error: err => this.notification.showHttpError(err)
      });
  }

  getDisponibilidadUsuario(
    usuarioId: number
  ): DisponibilidadUsuario | undefined {
    return this.disponibilidadUsuarios.get(usuarioId);
  }

  estaUsuarioDisponible(usuarioId: number): boolean {
    return this.getDisponibilidadUsuario(usuarioId)
      ?.disponible !== false;
  }

  getMotivoNoDisponible(motivo?: string | null): string {
    if (motivo === 'VACACIONES') return 'Vacaciones';
    if (motivo === 'AUSENCIA') return 'Ausente';
    if (motivo === 'CITA_ASIGNADA') return 'Otra cita asignada';
    return 'No disponible';
  }

  private fechaFinTecnica(fechaInicio: string): string {
    const inicio = new Date(fechaInicio);
    inicio.setMinutes(inicio.getMinutes() + this.duracionPredeterminada);

    const fecha = this.formatearFechaInput(inicio);
    const hora = this.formatearHoraInput(inicio);

    return `${fecha}T${hora}:00`;
  }

}
