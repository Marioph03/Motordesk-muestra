import {
  AfterViewInit,
  Component,
  ElementRef,
  EventEmitter,
  Output,
  ViewChild
} from '@angular/core';

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MatDialog } from '@angular/material/dialog';
import { inject } from '@angular/core';
import { DamageDialog } from '../../../../../../shared/components/damage-dialog/damage-dialog';

export interface Damage {

  scratch?: boolean;
  dent?: boolean;
  broken?: boolean;
  replace?: boolean;

}

export interface VehicleDamage {

  [piece: string]: Damage;

}

@Component({
  selector: 'app-vehicle-diagram-3d',
  standalone: true,
  templateUrl: './vehicle-diagram-3d.html',
  styleUrl: './vehicle-diagram-3d.scss'
})
export class VehicleDiagram3D implements AfterViewInit {

  @ViewChild('canvas', { static: true })
  canvasRef!: ElementRef<HTMLCanvasElement>;

  @ViewChild('viewer', { static: true })
  viewerRef!: ElementRef<HTMLDivElement>;

  private scene!: THREE.Scene;
  private camera!: THREE.PerspectiveCamera;
  private renderer!: THREE.WebGLRenderer;
  private controls!: OrbitControls;

  private raycaster = new THREE.Raycaster();
  private mouse = new THREE.Vector2();
  private meshes: THREE.Mesh[] = [];
  private readonly pieceLabels: Record<string, string> = {

  'hood_60': 'Capó',
  'trunk_99': 'Maletero',

  'bumper-front_8': 'Paragolpes delantero',
  'bumper-rear_10': 'Paragolpes trasero',

  'door-front-l_16': 'Puerta delantera izquierda',
  'door-front-r_17': 'Puerta delantera derecha',

  'door-rear-l_22': 'Puerta trasera izquierda',
  'door-rear-r_23': 'Puerta trasera derecha',

  'fender-front-l_32': 'Aleta delantera izquierda',
  'fender-front-r_33': 'Aleta delantera derecha',

  'side-mirror-l_70': 'Retrovisor izquierdo',
  'side-mirror-r_71': 'Retrovisor derecho',

  'headlights-cover-l_47': 'Faro delantero izquierdo',
  'headlights-cover-r_48': 'Faro delantero derecho',

  'taillight-lens-l_92': 'Piloto trasero izquierdo',
  'taillight-lens-r_89': 'Piloto trasero derecho',

  'windshield_102': 'Parabrisas',
  'glass-rear_42': 'Luneta trasera',

  'wheel-fender-l_100': 'Paso de rueda izquierdo',
  'wheel-fender-r_101': 'Paso de rueda derecho'

};

  private damages: VehicleDamage = {};
  private dialog = inject(MatDialog);
  @Output()
  damagesChange = new EventEmitter<VehicleDamage>();

  public getDamages(): VehicleDamage {

  return this.damages;

  }

  public setDamages(damages: VehicleDamage): void {

    this.damages = damages ?? {};

    if (this.meshes.length) {

      this.actualizarColores();

    }

  }

  ngAfterViewInit(): void {

    const esperarContenedor = () => {

      const viewer = this.viewerRef.nativeElement;

      if (viewer.offsetWidth === 0 || viewer.offsetHeight === 0) {
        requestAnimationFrame(esperarContenedor);
        return;
      }

      this.crearEscena();
      this.crearCamara();
      this.crearRenderer();
      this.crearLuces();
      this.crearControles();
      this.cargarModelo();

      this.animar();

      this.renderer.domElement.addEventListener(
        'pointerdown',
        this.onPointerDown.bind(this)
      );

    };

    esperarContenedor();

  }

  private crearEscena(): void {

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xf5f5f5);

    this.scene.add(new THREE.GridHelper(10, 10));

  }

  private crearCamara(): void {

    const viewer = this.viewerRef.nativeElement;
    const rect = viewer.getBoundingClientRect();

    this.camera = new THREE.PerspectiveCamera(
      60,
      rect.width / rect.height,
      0.1,
      1000
    );

    this.camera.position.set(0, 1.5, 6);

  }

  private crearRenderer(): void {

    const canvas = this.canvasRef.nativeElement;
    const viewer = this.viewerRef.nativeElement;

    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true
    });

    this.renderer.setPixelRatio(window.devicePixelRatio);

    const rect = viewer.getBoundingClientRect();

    this.renderer.setSize(rect.width, rect.height, false);

    this.camera.aspect = rect.width / rect.height;
    this.camera.updateProjectionMatrix();

  }

  private crearLuces(): void {

    const ambient = new THREE.AmbientLight(0xffffff, 2);
    this.scene.add(ambient);

    const dir1 = new THREE.DirectionalLight(0xffffff, 3);
    dir1.position.set(10, 10, 10);
    this.scene.add(dir1);

    const dir2 = new THREE.DirectionalLight(0xffffff, 2);
    dir2.position.set(-10, 10, -10);
    this.scene.add(dir2);

  }

  private crearControles(): void {

    this.controls = new OrbitControls(
      this.camera,
      this.renderer.domElement
    );

    this.controls.enableDamping = true;
    this.controls.target.set(0, 0.5, 0);
    this.controls.update();

  }

  private cargarModelo(): void {

  const loader = new GLTFLoader();

  loader.load(

    'assets/models/car.glb',

    (gltf) => {

      const modelo = gltf.scene;

      modelo.traverse((objeto) => {

        if (objeto instanceof THREE.Mesh) {

          if (objeto.material) {

            if (Array.isArray(objeto.material)) {

              objeto.material = objeto.material.map(
                material => material.clone()
              );

            } else {

              objeto.material = objeto.material.clone();

            }

          }

          this.meshes.push(objeto);

        }

      });

      const box = new THREE.Box3().setFromObject(modelo);
      const size = box.getSize(new THREE.Vector3());
      const center = box.getCenter(new THREE.Vector3());

      modelo.position.sub(center);

      const maxDimension = Math.max(
        size.x,
        size.y,
        size.z
      );

      const escala = 4 / maxDimension;

      modelo.scale.setScalar(escala);

      const nuevaCaja = new THREE.Box3().setFromObject(modelo);
      const minY = nuevaCaja.min.y;

      modelo.position.y -= minY;

      this.scene.add(modelo);

      this.actualizarColores();

      console.log('Modelo cargado correctamente');

    },

    undefined,

    (error) => {

      console.error(
        'Error cargando el modelo:',
        error
      );

    }

  );
  }

  private animar(): void {

    const render = () => {

      requestAnimationFrame(render);

      this.controls.update();

      this.renderer.render(
        this.scene,
        this.camera
      );

    };

    render();

  }

  private onPointerDown(event: PointerEvent): void {

  const rect = this.renderer.domElement.getBoundingClientRect();

  this.mouse.x =
    ((event.clientX - rect.left) / rect.width) * 2 - 1;

  this.mouse.y =
    -((event.clientY - rect.top) / rect.height) * 2 + 1;

  this.raycaster.setFromCamera(
    this.mouse,
    this.camera
  );

  const hits = this.raycaster.intersectObjects(
    this.meshes,
    true
  );

  if (!hits.length) {
    return;
  }

  const mesh = hits[0].object as THREE.Mesh;

  console.log('Mesh pulsado:', mesh.name);
  console.log('Padre:', mesh.parent?.name);
  console.log('Material:', mesh.material);
  console.log('Tipo material:', (mesh.material as any).type);

  // Identificador real de la pieza dentro del GLB
  const piece = mesh.parent?.name ?? mesh.name;

  // Nombre que verá el usuario
  const pieceLabel = this.pieceLabels[piece];

  console.log(
    'Pieza:',
    piece,
    '| Nombre:',
    pieceLabel ?? 'No configurable'
  );

  // Solo permitimos registrar daños en las piezas
  // que hemos definido en pieceLabels
  if (!pieceLabel) {

    console.log(
      'Pieza no configurable para daños:',
      piece
    );

    return;

  }

  const dialogRef = this.dialog.open(DamageDialog, {
    width: '400px',
    data: {
      piece: pieceLabel
    }
  });

  dialogRef.afterClosed().subscribe(result => {

    if (!result) {
      return;
    }

    // IMPORTANTE:
    // Guardamos la clave técnica del GLB, no el nombre español.
    this.damages[piece] = {
      [result]: true
    };

    this.actualizarColores();

    // Avisamos al componente padre de que han cambiado los daños
    this.damagesChange.emit({
      ...this.damages
    });

    console.log(
      'Daños actualizados:',
      this.damages
    );

  });

  }

  private actualizarColores(): void {

  this.meshes.forEach(mesh => {

    const material = mesh.material as THREE.MeshStandardMaterial;

    const piece = mesh.parent?.name ?? mesh.name;

    const damage = this.damages[piece];

    // Restaurar estado
    material.color.setHex(0xffffff);
    material.emissive.setHex(0x000000);
    material.emissiveIntensity = 1;

    if (damage) {

      if (damage.scratch) {

        material.emissive.setHex(0xffff00);

      } else if (damage.dent) {

        material.emissive.setHex(0xff9800);

      } else if (damage.broken) {

        material.emissive.setHex(0x2196f3);

      } else if (damage.replace) {

        material.emissive.setHex(0xff0000);

      }

    }

    material.needsUpdate = true;

  });

  }

}
/** Diagrama interactivo usado para registrar inspecciones visuales de daños. */
