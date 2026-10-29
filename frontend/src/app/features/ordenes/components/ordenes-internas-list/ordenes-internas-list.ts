import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { finalize, timeout } from 'rxjs';
import { MatButtonModule } from '@angular/material/button'; import { MatCardModule } from '@angular/material/card'; import { MatIconModule } from '@angular/material/icon'; import { MatTableModule } from '@angular/material/table'; import { MatChipsModule } from '@angular/material/chips';
import { OrdenInterna } from '../../models/orden-interna'; import { OrdenesInternasService } from '../../services/ordenes-internas.service'; import { NotificationService } from '../../../../shared/services/notification';
@Component({ selector: 'app-ordenes-internas-list', standalone: true, imports: [CommonModule, RouterLink, MatButtonModule, MatCardModule, MatIconModule, MatTableModule, MatChipsModule], templateUrl: './ordenes-internas-list.html', styleUrl: './ordenes-internas-list.scss' })
export class OrdenesInternasList implements OnInit { private readonly service=inject(OrdenesInternasService); private readonly notification=inject(NotificationService); private readonly cdr=inject(ChangeDetectorRef); ordenes: OrdenInterna[]=[]; cargando=true; columnas=['numero','trabajo','categoria','estado','coste','acciones']; ngOnInit(){ this.service.listar().pipe(timeout(12_000),finalize(()=>{this.cargando=false;this.cdr.detectChanges()})).subscribe({next:ordenes=>{this.ordenes=ordenes;this.cdr.markForCheck()},error:error=>this.notification.showHttpError(error)}); } }
