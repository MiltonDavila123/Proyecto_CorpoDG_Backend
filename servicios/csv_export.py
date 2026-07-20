"""Generación de CSV de reservas (usado por la acción del admin y la
página de exportación por rango de fechas)."""
import csv
import json

from django.http import HttpResponse


def csv_response_reservas(model, queryset, sufijo=''):
    """Arma la respuesta CSV con todos los campos del modelo de reserva.

    Con BOM y separador ';' para que Excel lo abra bien con acentos.
    """
    campos = list(model._meta.fields)
    nombre_archivo = f"{model._meta.model_name}{sufijo}.csv"

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    response.write('\ufeff')  # BOM para que Excel abra bien los acentos

    writer = csv.writer(response, delimiter=';')
    writer.writerow([f.verbose_name for f in campos])
    for reserva in queryset:
        fila = []
        for f in campos:
            valor = getattr(reserva, f.name)
            if isinstance(valor, (dict, list)):
                valor = json.dumps(valor, ensure_ascii=False)
            fila.append('' if valor is None else valor)
        writer.writerow(fila)
    return response
