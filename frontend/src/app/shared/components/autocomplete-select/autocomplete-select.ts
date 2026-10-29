import {
  Component,
  EventEmitter,
  Input,
  Output,
  forwardRef
} from '@angular/core';
import {
  ControlValueAccessor,
  NG_VALUE_ACCESSOR
} from '@angular/forms';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';


@Component({
  selector: 'app-autocomplete-select',
  standalone: true,
  imports: [
    MatAutocompleteModule,
    MatFormFieldModule,
    MatInputModule
  ],
  templateUrl: './autocomplete-select.html',
  styleUrl: './autocomplete-select.scss',
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(
        () => AutocompleteSelect
      ),
      multi: true
    }
  ]
})
export class AutocompleteSelect<T extends { id: number }>
  implements ControlValueAccessor {

  @Input() etiqueta = 'Seleccionar';
  @Input() placeholder = 'Escribe para buscar';
  @Input() items: readonly T[] = [];
  @Input() mostrar: (item: T) => string = item => String(item.id);
  @Output() seleccionado = new EventEmitter<number | null>();

  texto = '';
  disabled = false;

  private valor: number | null = null;
  private onChange: (valor: number | null) => void = () => undefined;
  private onTouched: () => void = () => undefined;

  get resultados(): readonly T[] {
    const busqueda = this.texto.trim().toLocaleLowerCase();

    if (!busqueda) {
      return this.items;
    }

    return this.items.filter(item =>
      this.mostrar(item)
        .toLocaleLowerCase()
        .includes(busqueda)
    );
  }

  writeValue(valor: number | null): void {
    this.valor = valor;
    this.actualizarTexto();
  }

  registerOnChange(fn: (valor: number | null) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(disabled: boolean): void {
    this.disabled = disabled;
  }

  escribir(valor: string): void {
    this.texto = valor;

    if (this.valor !== null) {
      this.valor = null;
      this.onChange(null);
      this.seleccionado.emit(null);
    }
  }

  seleccionar(id: number): void {
    this.valor = id;
    this.onChange(id);
    this.seleccionado.emit(id);
    this.actualizarTexto();
  }

  marcarTocado(): void {
    this.onTouched();
  }

  ngOnChanges(): void {
    this.actualizarTexto();
  }

  private actualizarTexto(): void {
    const seleccionado = this.items.find(
      item => item.id === this.valor
    );

    if (seleccionado) {
      this.texto = this.mostrar(seleccionado);
    } else if (this.valor === null || this.valor === 0) {
      this.texto = '';
    }
  }
}
/** Selector reutilizable con filtrado incremental para catálogos extensos. */
