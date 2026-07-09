from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import timedelta

from .models import (
    Destino, Vuelo, Region, PaisRegion, Ciudad, Aerolinea, Aeropuerto,
    PaqueteTuristico, ConfiguracionDestacados, TipoPaquete, Temporada, validate_google_drive_pdf,
    validate_openstreetmap_url, normalize_google_drive_url,
)
from .searchFlights import (
    _construir_ids_fuente, formatear_duracion, procesar_respuesta,
    buscar_vuelos_sabre,
)
from .revalidateFlight import (
    _normalizar_segmento as reval_normalizar_segmento,
    _construir_payload as reval_construir_payload,
    revalidar_itinerario,
)
from .seatMapFlight import (
    _sandbox_activo, _normalizar_segmento as seat_normalizar_segmento,
    _construir_payload as seat_construir_payload,
    obtener_mapa_asientos,
)
from .chatbot import _build_accion, ejecutar_tool, procesar_mensaje


# ============================================================
# TESTS DE MODELOS
# ============================================================

class ValidateGoogleDrivePdfTest(TestCase):
    def test_url_valida_retorna_url(self):
        url = "https://drive.google.com/file/d/abc123/view"
        self.assertEqual(validate_google_drive_pdf(url), url)

    def test_url_preview_valida(self):
        url = "https://drive.google.com/file/d/abc123/preview"
        self.assertEqual(validate_google_drive_pdf(url), url)

    def test_url_edit_valida(self):
        url = "https://drive.google.com/file/d/abc123/edit"
        self.assertEqual(validate_google_drive_pdf(url), url)

    def test_url_invalida_raise_error(self):
        with self.assertRaises(ValidationError):
            validate_google_drive_pdf("https://example.com/file.pdf")

    def test_url_vacia_retorna_vacio(self):
        self.assertIsNone(validate_google_drive_pdf(None))
        self.assertEqual(validate_google_drive_pdf(""), "")


class ValidateOpenstreetmapUrlTest(TestCase):
    def test_url_valida_retorna_url(self):
        url = "https://www.openstreetmap.org/#map=11/4.6497/-74.1165"
        self.assertEqual(validate_openstreetmap_url(url), url)

    def test_url_sin_www_valida(self):
        url = "https://openstreetmap.org/#map=11/4.6497/-74.1165"
        self.assertEqual(validate_openstreetmap_url(url), url)

    def test_url_invalida_raise_error(self):
        with self.assertRaises(ValidationError):
            validate_openstreetmap_url("https://maps.google.com/")

    def test_url_vacia_retorna_vacio(self):
        self.assertIsNone(validate_openstreetmap_url(None))
        self.assertEqual(validate_openstreetmap_url(""), "")


class NormalizeGoogleDriveUrlTest(TestCase):
    def test_view_to_preview(self):
        self.assertEqual(
            normalize_google_drive_url("https://drive.google.com/file/d/abc123/view"),
            "https://drive.google.com/file/d/abc123/preview"
        )

    def test_edit_to_preview(self):
        self.assertEqual(
            normalize_google_drive_url("https://drive.google.com/file/d/abc123/edit"),
            "https://drive.google.com/file/d/abc123/preview"
        )

    def test_preview_stays_preview(self):
        url = "https://drive.google.com/file/d/abc123/preview"
        self.assertEqual(normalize_google_drive_url(url), url)

    def test_none_retorna_none(self):
        self.assertIsNone(normalize_google_drive_url(None))


class DestinoModelCleanTest(TestCase):
    def setUp(self):
        self.region = Region.objects.create(nombre="sudamerica", orden=1)
        self.pais = PaisRegion.objects.create(region=self.region, nombre="Ecuador", codigo_iso="EC")
        self.ciudad = Ciudad.objects.create(pais=self.pais, nombre="Quito", codigo_ciudad="UIO")

    def test_destino_valido_pais_y_ciudad(self):
        d = Destino(
            nombre="Test", pais=self.pais, ciudad=self.ciudad,
            descripcion="Desc", imagen_url="https://example.com/img.jpg",
            precio_desde=Decimal("100"), activo=True
        )
        d.clean()
        self.assertEqual(d.pais, self.pais)

    def test_destino_con_ciudad_de_otro_pais_raise_error(self):
        otro_pais = PaisRegion.objects.create(region=self.region, nombre="Peru", codigo_iso="PE")
        d = Destino(
            nombre="Test", pais=otro_pais, ciudad=self.ciudad,
            descripcion="Desc", imagen_url="https://example.com/img.jpg",
            precio_desde=Decimal("100"), activo=True
        )
        with self.assertRaises(ValidationError):
            d.clean()

    def test_destino_sin_pais_ni_ciudad_raise_error(self):
        d = Destino(
            nombre="Test",
            descripcion="Desc", imagen_url="https://example.com/img.jpg",
            precio_desde=Decimal("100"), activo=True
        )
        with self.assertRaises(ValidationError):
            d.clean()

    def test_destino_con_ciudad_autocompleta_pais(self):
        d = Destino(
            nombre="Test", ciudad=self.ciudad,
            descripcion="Desc", imagen_url="https://example.com/img.jpg",
            precio_desde=Decimal("100"), activo=True
        )
        d.clean()
        self.assertEqual(d.pais, self.pais)


class PaqueteTuristicoVencimientoTest(TestCase):
    def setUp(self):
        self.region = Region.objects.create(nombre="caribe", orden=1)
        self.pais = PaisRegion.objects.create(region=self.region, nombre="Republica Dominicana", codigo_iso="DO")

    def test_esta_vencido_sin_fecha_retorna_false(self):
        p = PaqueteTuristico(
            titulo="Test", region=self.region, pais_destino=self.pais,
            precio=Decimal("500"), duracion_noches=5, salidas="Quito",
            imagen_url="https://example.com/img.jpg",
            descripcion_corta="Desc"
        )
        self.assertFalse(p.esta_vencido)

    def test_esta_vencido_con_fecha_futura_retorna_false(self):
        p = PaqueteTuristico(
            titulo="Test", region=self.region, pais_destino=self.pais,
            precio=Decimal("500"), duracion_noches=5, salidas="Quito",
            imagen_url="https://example.com/img.jpg",
            descripcion_corta="Desc",
            precio_aplica_hasta=timezone.localdate() + timedelta(days=30)
        )
        self.assertFalse(p.esta_vencido)

    def test_esta_vencido_con_fecha_pasada_retorna_true(self):
        p = PaqueteTuristico(
            titulo="Test", region=self.region, pais_destino=self.pais,
            precio=Decimal("500"), duracion_noches=5, salidas="Quito",
            imagen_url="https://example.com/img.jpg",
            descripcion_corta="Desc",
            precio_aplica_hasta=timezone.localdate() - timedelta(days=1)
        )
        self.assertTrue(p.esta_vencido)

    def test_sincronizar_vigencia_desactiva_vencidos(self):
        p = PaqueteTuristico.objects.create(
            titulo="Test", region=self.region, pais_destino=self.pais,
            precio=Decimal("500"), duracion_noches=5, salidas="Quito",
            imagen_url="https://example.com/img.jpg",
            descripcion_corta="Desc",
            activo=True,
            precio_aplica_hasta=timezone.localdate() - timedelta(days=1)
        )
        desactivados, reactivados = PaqueteTuristico.sincronizar_vigencia()
        self.assertEqual(desactivados, 1)
        p.refresh_from_db()
        self.assertFalse(p.activo)

    def test_sincronizar_vigencia_reactiva_vigentes(self):
        p = PaqueteTuristico.objects.create(
            titulo="Test", region=self.region, pais_destino=self.pais,
            precio=Decimal("500"), duracion_noches=5, salidas="Quito",
            imagen_url="https://example.com/img.jpg",
            descripcion_corta="Desc",
            activo=False,
            precio_aplica_hasta=timezone.localdate() + timedelta(days=30)
        )
        desactivados, reactivados = PaqueteTuristico.sincronizar_vigencia()
        self.assertEqual(reactivados, 1)
        p.refresh_from_db()
        self.assertTrue(p.activo)


class ConfiguracionDestacadosTest(TestCase):
    def test_load_crea_si_no_existe(self):
        self.assertEqual(ConfiguracionDestacados.objects.count(), 0)
        config = ConfiguracionDestacados.load()
        self.assertEqual(ConfiguracionDestacados.objects.count(), 1)
        self.assertEqual(config.limite_vuelos, 10)
        self.assertEqual(config.limite_paquetes, 10)
        self.assertEqual(config.limite_destinos, 10)

    def test_load_retorna_existente(self):
        ConfiguracionDestacados.objects.create(limite_vuelos=5, limite_paquetes=3, limite_destinos=2)
        config = ConfiguracionDestacados.load()
        self.assertEqual(config.limite_vuelos, 5)


# ============================================================
# TESTS DE SEARCH FLIGHTS
# ============================================================

class ConstruirIdsFuenteTest(TestCase):
    def test_con_id_itinerario(self):
        prov, id_f, id_u = _construir_ids_fuente("sabre", 42, 0)
        self.assertEqual(prov, "sabre")
        self.assertEqual(id_f, "42")
        self.assertEqual(id_u, "sabre:42")

    def test_sin_id_itinerario(self):
        prov, id_f, id_u = _construir_ids_fuente("sabre", None, 5)
        self.assertEqual(id_f, "idx-5")
        self.assertEqual(id_u, "sabre:idx-5")

    def test_proveedor_none(self):
        prov, _, _ = _construir_ids_fuente(None, 1, 0)
        self.assertEqual(prov, "desconocido")


class FormatearDuracionTest(TestCase):
    def test_solo_horas(self):
        self.assertEqual(formatear_duracion(120), "2h 0m")

    def test_horas_y_minutos(self):
        self.assertEqual(formatear_duracion(150), "2h 30m")

    def test_menos_de_una_hora(self):
        self.assertEqual(formatear_duracion(45), "0h 45m")

    def test_cero(self):
        self.assertEqual(formatear_duracion(0), "0h 0m")


class ProcesarRespuestaSortTest(TestCase):
    """Verifica el orden: escalas -> duracion -> precio"""

    def _make_sabre_response(self, itinerarios_data):
        schedules = []
        legs = []
        itinerary_groups = {"groupDescription": {"legDescriptions": []}, "itineraries": []}

        for idx, it_data in enumerate(itinerarios_data):
            precio_total = it_data.get("precio_total", "100")
            escalas = it_data.get("escalas", 0)
            duracion = it_data.get("duracion", 60)

            seg_ids = []
            for s in range(escalas + 1):
                sid = f"SCH-{idx}-{s}"
                sch = {
                    "id": sid,
                    "departure": {"airport": "UIO", "time": "10:00"},
                    "arrival": {"airport": "MIA", "time": "15:00"},
                    "carrier": {"marketing": "AA", "marketingFlightNumber": "1000"},
                    "elapsedTime": duracion // (escalas + 1) if (escalas + 1) else duracion,
                }
                schedules.append(sch)
                seg_ids.append({"ref": sid, "bookingClass": "Y", "cabin": "Y"})

            lid = f"LEG-{idx}"
            legs.append({"id": lid, "schedules": seg_ids, "elapsedTime": duracion})

            itinerary_groups["itineraries"].append({
                "id": idx,
                "legs": [{"ref": lid}],
                "pricingInformation": [{
                    "fare": {
                        "totalFare": {"totalPrice": str(precio_total), "currency": "USD",
                                      "baseFareAmount": str(precio_total), "totalTaxAmount": "0"},
                        "validatingCarrierCode": "AA",
                        "totalFare": {"totalPrice": str(precio_total), "currency": "USD"},
                        "passengerInfoList": [{
                            "passengerInfo": {"fareComponents": []}
                        }]
                    }
                }],
            })

        return {
            "groupedItineraryResponse": {
                "scheduleDescs": schedules,
                "legDescs": legs,
                "itineraryGroups": [itinerary_groups],
                "statistics": {"itineraryCount": len(itinerarios_data)},
            }
        }

    def test_ordena_por_escalas_primero(self):
        data = self._make_sabre_response([
            {"precio_total": "500", "escalas": 1, "duracion": 200},
            {"precio_total": "600", "escalas": 0, "duracion": 150},
        ])
        result = procesar_respuesta(data)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[1]["id"], 0)

    def test_ordena_por_duracion_segundo(self):
        data = self._make_sabre_response([
            {"precio_total": "500", "escalas": 0, "duracion": 200},
            {"precio_total": "500", "escalas": 0, "duracion": 150},
        ])
        result = procesar_respuesta(data)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[1]["id"], 0)

    def test_ordena_por_precio_tercero(self):
        data = self._make_sabre_response([
            {"precio_total": "500", "escalas": 0, "duracion": 150},
            {"precio_total": "300", "escalas": 0, "duracion": 150},
        ])
        result = procesar_respuesta(data)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[1]["id"], 0)

    def test_sin_itineraries_retorna_lista_vacia(self):
        result = procesar_respuesta({"groupedItineraryResponse": {"itineraryGroups": []}})
        self.assertEqual(result, [])


class BuscarVuelosSabre401RetryTest(TestCase):
    @patch("servicios.searchFlights._buscar_en_sabre")
    def test_401_retry_con_force_refresh(self, mock_buscar):
        mock_unauthorized = MagicMock()
        mock_unauthorized.status_code = 401
        mock_unauthorized.json.return_value = {"error": "Token expired"}

        mock_success = MagicMock()
        mock_success.status_code = 200
        mock_success.json.return_value = {
            "groupedItineraryResponse": {
                "itineraryGroups": [{
                    "groupDescription": {"legDescriptions": []},
                    "itineraries": []
                }],
                "statistics": {"itineraryCount": 0}
            }
        }

        mock_buscar.side_effect = [mock_unauthorized, mock_success]

        datos = {
            "origin": "UIO", "destination": "MIA",
            "date": "2026-09-15", "adults": 1
        }
        result = buscar_vuelos_sabre(datos)

        self.assertEqual(mock_buscar.call_count, 2)
        self.assertEqual(result, [])

    @patch("servicios.searchFlights._buscar_en_sabre")
    def test_200_no_retry(self, mock_buscar):
        mock_ok = MagicMock()
        mock_ok.status_code = 200
        mock_ok.json.return_value = {
            "groupedItineraryResponse": {
                "itineraryGroups": [{
                    "groupDescription": {"legDescriptions": []},
                    "itineraries": []
                }],
                "statistics": {"itineraryCount": 0}
            }
        }
        mock_buscar.return_value = mock_ok

        result = buscar_vuelos_sabre({"origin": "UIO", "destination": "MIA", "date": "2026-09-15", "adults": 1})
        self.assertEqual(mock_buscar.call_count, 1)

    @patch("servicios.searchFlights._buscar_en_sabre")
    def test_doble_401_retorna_error(self, mock_buscar):
        mock_err = MagicMock()
        mock_err.status_code = 401
        mock_err.json.return_value = {"error": "Token expired"}
        mock_buscar.return_value = mock_err

        datos = {"origin": "UIO", "destination": "MIA", "date": "2026-09-15", "adults": 1}
        result = buscar_vuelos_sabre(datos)
        self.assertIn("error", result)
        self.assertEqual(result["code"], 401)


# ============================================================
# TESTS DE REVALIDATE FLIGHT
# ============================================================

class RevalidateNormalizarSegmentoTest(TestCase):
    def test_formato_enriquecido(self):
        seg = {
            "salida": {"aeropuerto": "UIO"},
            "llegada": {"aeropuerto": "MIA"},
            "aerolinea": {"codigo": "AA", "operada_por": "AA"},
            "numero_vuelo": 1000,
            "clase_servicio": "Y",
            "fecha_hora_salida": "2026-09-15T10:00:00",
            "fecha_hora_llegada": "2026-09-15T15:00:00",
        }
        result = reval_normalizar_segmento(seg)
        self.assertEqual(result["origen"], "UIO")
        self.assertEqual(result["destino"], "MIA")
        self.assertEqual(result["marketing"], "AA")
        self.assertEqual(result["numero_vuelo"], 1000)

    def test_vuelo_string_extrae_numero(self):
        seg = {
            "aerolinea": {"codigo": "AA"},
            "vuelo": "AA833",
            "clase_servicio": "Y",
            "fecha_hora_salida": "2026-09-15T10:00:00",
            "fecha_hora_llegada": "2026-09-15T15:00:00",
        }
        result = reval_normalizar_segmento(seg)
        self.assertEqual(result["numero_vuelo"], 833)

    def test_segmento_incompleto_numero_none(self):
        seg = {"clase_servicio": "Y", "fecha_hora_salida": "2026-09-15T10:00:00", "fecha_hora_llegada": "2026-09-15T15:00:00"}
        result = reval_normalizar_segmento(seg)
        self.assertIsNone(result["numero_vuelo"])
        self.assertIsNone(result["origen"])
        self.assertIsNone(result["destino"])


class RevalidateConstruirPayloadTest(TestCase):
    def test_payload_valido(self):
        tramos = [{
            "segmentos": [{
                "origen": "UIO", "destino": "MIA",
                "aerolinea": {"codigo": "AA"},
                "numero_vuelo": 1000,
                "clase_servicio": "Y",
                "fecha_hora_salida": "2026-09-15T10:00:00",
                "fecha_hora_llegada": "2026-09-15T15:00:00",
            }]
        }]
        pasajeros = {"adults": 1, "children": 0, "infants": 0}
        payload = reval_construir_payload(tramos, pasajeros)
        rq = payload["OTA_AirLowFareSearchRQ"]
        self.assertEqual(len(rq["OriginDestinationInformation"]), 1)
        self.assertEqual(rq["TravelerInfoSummary"]["AirTravelerAvail"][0]["PassengerTypeQuantity"][0]["Code"], "ADT")

    def test_sin_tramos_raise_error(self):
        with self.assertRaises(ValueError):
            reval_construir_payload([{"segmentos": []}], {"adults": 1})

    def test_campos_faltantes_raise_error(self):
        tramos = [{
            "segmentos": [{
                "origen": "UIO", "destino": "MIA",
                "aerolinea": {"codigo": "AA"},
                "numero_vuelo": 1000,
                # falta clase_servicio, fecha_hora_salida, fecha_hora_llegada
            }]
        }]
        with self.assertRaises(ValueError):
            reval_construir_payload(tramos, {"adults": 1})

    def test_payload_sin_pasajeros_default_adult(self):
        tramos = [{
            "segmentos": [{
                "origen": "UIO", "destino": "MIA",
                "aerolinea": {"codigo": "AA"},
                "numero_vuelo": 1000,
                "clase_servicio": "Y",
                "fecha_hora_salida": "2026-09-15T10:00:00",
                "fecha_hora_llegada": "2026-09-15T15:00:00",
            }]
        }]
        payload = reval_construir_payload(tramos, {"adults": 0, "children": 0, "infants": 0})
        rq = payload["OTA_AirLowFareSearchRQ"]
        self.assertEqual(
            rq["TravelerInfoSummary"]["AirTravelerAvail"][0]["PassengerTypeQuantity"][0]["Code"], "ADT"
        )


class RevalidarItinerarioTest(TestCase):
    def test_sin_tramos_retorna_error(self):
        result = revalidar_itinerario({"tramos": []})
        self.assertFalse(result["disponible"])
        self.assertEqual(result["code"], 400)

    @patch("servicios.revalidateFlight._llamar_revalidate")
    def test_401_retry(self, mock_llamar):
        mock_401 = MagicMock()
        mock_401.status_code = 401
        mock_200_val = {
            "groupedItineraryResponse": {
                "statistics": {"itineraryCount": 1},
                "itineraryGroups": [{
                    "itineraries": [{
                        "pricingInformation": [{
                            "fare": {"totalFare": {"totalPrice": "500", "currency": "USD"}}
                        }]
                    }]
                }]
            }
        }
        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.json.return_value = mock_200_val

        mock_llamar.side_effect = [mock_401, mock_200]

        datos = {
            "tramos": [{
                "segmentos": [{
                    "origen": "UIO", "destino": "MIA",
                    "aerolinea": {"codigo": "AA"},
                    "numero_vuelo": 1000,
                    "clase_servicio": "Y",
                    "fecha_hora_salida": "2026-09-15T10:00:00",
                    "fecha_hora_llegada": "2026-09-15T15:00:00",
                }]
            }],
            "adults": 1
        }
        result = revalidar_itinerario(datos)
        self.assertTrue(result["disponible"])
        self.assertEqual(mock_llamar.call_count, 2)


# ============================================================
# TESTS DE SEAT MAP FLIGHT
# ============================================================

class SandboxActivoTest(TestCase):
    @override_settings(SEATMAP_SANDBOX=True)
    def test_sandbox_true_desde_settings(self):
        self.assertTrue(_sandbox_activo())

    @override_settings(SEATMAP_SANDBOX=False)
    def test_sandbox_false_desde_settings(self):
        self.assertFalse(_sandbox_activo())

    @override_settings()  # limpia el setting
    def test_sandbox_default_true_cuando_no_configurado(self):
        self.assertTrue(_sandbox_activo())


class SeatNormalizarSegmentoTest(TestCase):
    def test_formato_enriquecido(self):
        seg = {
            "salida": {"aeropuerto": "UIO"},
            "llegada": {"aeropuerto": "MIA"},
            "aerolinea": {"codigo": "AA"},
            "numero_vuelo": 1000,
            "clase_servicio": "Y",
            "cabina": "Y",
            "fecha_hora_salida": "2026-09-15T10:00:00",
            "fecha_hora_llegada": "2026-09-15T15:00:00",
        }
        result = seat_normalizar_segmento(seg)
        self.assertEqual(result["origen"], "UIO")
        self.assertEqual(result["destino"], "MIA")
        self.assertEqual(result["fecha_salida"], "2026-09-15")

    def test_vuelo_string_extrae_numero(self):
        seg = {
            "aerolinea": {"codigo": "AA"},
            "vuelo": "AA833",
            "clase_servicio": "Y",
            "fecha_hora_salida": "2026-09-15T10:00:00",
            "fecha_hora_llegada": "2026-09-15T15:00:00",
        }
        result = seat_normalizar_segmento(seg)
        self.assertEqual(result["numero_vuelo"], 833)


class SeatConstruirPayloadTest(TestCase):
    def _make_opcion(self):
        return {
            "tramos": [{
                "segmentos": [{
                    "origen": "UIO", "destino": "MIA",
                    "aerolinea": {"codigo": "AA"},
                    "numero_vuelo": 1000,
                    "numero_vuelo_operador": 1000,
                    "clase_servicio": "Y", "cabina": "Y",
                    "fare_basis": "YLF7R",
                    "fecha_salida": "2026-09-15",
                    "fecha_llegada": "2026-09-15",
                    "hora_salida": "10:00", "hora_llegada": "15:00",
                    "fecha_hora_salida": "2026-09-15T10:00:00",
                    "fecha_hora_llegada": "2026-09-15T15:00:00",
                }]
            }],
            "fare_info": [{
                "end": "MIA",
                "governing_carrier": "AA",
                "fare_amount": "500",
                "fare_currency": "USD",
                "cabin": "Y",
            }],
            "precio_base": "500",
            "moneda": "USD",
        }

    def test_payload_valido(self):
        opcion = self._make_opcion()
        pasajeros = [{"passengerType": "ADT", "givenName": "TEST", "surname": "TEST"}]
        payload, seg_ids, pax_ids = seat_construir_payload(opcion, pasajeros, "USD")
        self.assertIn("segments", payload)
        self.assertIn("passengers", payload)
        self.assertEqual(len(payload["segments"]), 1)
        self.assertEqual(len(payload["passengers"]), 1)

    def test_sin_tramos_raise_error(self):
        with self.assertRaises(ValueError):
            seat_construir_payload({"tramos": []}, [], "USD")

    def test_sin_fare_info_raise_error(self):
        opcion = self._make_opcion()
        opcion["fare_info"] = []
        with self.assertRaises(ValueError):
            seat_construir_payload(opcion, [{"passengerType": "ADT"}], "USD")


class ObtenerMapaAsientosTest(TestCase):
    @override_settings(SEATMAP_SANDBOX=True)
    def test_sin_opcion_retorna_error(self):
        result = obtener_mapa_asientos({"opcion": {}})
        self.assertIn("error", result)
        self.assertEqual(result["code"], 400)

    @override_settings(SEATMAP_SANDBOX=True)
    def test_sandbox_retorna_mapa_con_warnings(self):
        opcion = {
            "tramos": [{
                "segmentos": [{
                    "origen": "UIO", "destino": "MIA",
                    "aerolinea": {"codigo": "AA"},
                    "numero_vuelo": 1000,
                    "numero_vuelo_operador": 1000,
                    "clase_servicio": "Y", "cabina": "Y",
                    "fare_basis": "YLF7R",
                    "fecha_salida": "2026-09-15",
                    "fecha_llegada": "2026-09-15",
                    "hora_salida": "10:00", "hora_llegada": "15:00",
                    "fecha_hora_salida": "2026-09-15T10:00:00",
                    "fecha_hora_llegada": "2026-09-15T15:00:00",
                }]
            }],
            "fare_info": [{"end": "MIA", "governing_carrier": "AA", "fare_amount": "500", "fare_currency": "USD", "cabin": "Y"}],
            "precio_base": "500", "moneda": "USD",
        }
        result = obtener_mapa_asientos({"opcion": opcion, "sandbox": True})
        self.assertIn("mapas", result)
        self.assertTrue(result.get("sandbox"))
        self.assertIsInstance(result["mapas"], list)


# ============================================================
# TESTS DE VIEWSETS (catálogo)
# ============================================================

class DestinoViewSetFilterTest(TestCase):
    def setUp(self):
        self.region = Region.objects.create(nombre="sudamerica", orden=1)
        self.pais_ec = PaisRegion.objects.create(region=self.region, nombre="Ecuador", codigo_iso="EC")
        self.pais_pe = PaisRegion.objects.create(region=self.region, nombre="Peru", codigo_iso="PE")
        self.ciudad_gye = Ciudad.objects.create(pais=self.pais_ec, nombre="Guayaquil", codigo_ciudad="GYE")
        self.ciudad_uio = Ciudad.objects.create(pais=self.pais_ec, nombre="Quito", codigo_ciudad="UIO")

        self.d1 = Destino.objects.create(
            nombre="Galapagos", pais=self.pais_ec, ciudad=self.ciudad_gye,
            descripcion="Islas", imagen_url="https://example.com/img.jpg",
            precio_desde=Decimal("800"), activo=True, destacado=True
        )
        self.d2 = Destino.objects.create(
            nombre="Quito Colonial", pais=self.pais_ec, ciudad=self.ciudad_uio,
            descripcion="Ciudad", imagen_url="https://example.com/img.jpg",
            precio_desde=Decimal("300"), activo=True, destacado=False
        )
        self.d3 = Destino.objects.create(
            nombre="Machu Picchu", pais=self.pais_pe,
            descripcion="Ruinas", imagen_url="https://example.com/img.jpg",
            precio_desde=Decimal("500"), activo=False
        )

    def test_solo_activos(self):
        qs = Destino.objects.filter(activo=True)
        self.assertEqual(qs.count(), 2)

    def test_filtro_por_pais(self):
        qs = Destino.objects.filter(activo=True, pais_id=self.pais_ec.id)
        self.assertEqual(qs.count(), 2)

    def test_filtro_por_ciudad(self):
        qs = Destino.objects.filter(activo=True, ciudad_id=self.ciudad_gye.id)
        self.assertEqual(qs.count(), 1)

    def test_filtro_destacados(self):
        qs = Destino.objects.filter(activo=True, destacado=True)
        self.assertEqual(qs.count(), 1)


class PaqueteTuristicoViewSetFilterTest(TestCase):
    def setUp(self):
        self.region = Region.objects.create(nombre="caribe", orden=1)
        self.pais = PaisRegion.objects.create(region=self.region, nombre="RD", codigo_iso="DO")
        self.tipo = TipoPaquete.objects.create(nombre="Vacaciones")
        self.temp = Temporada.objects.create(nombre="Temporada Alta")

        self.p1 = PaqueteTuristico.objects.create(
            titulo="Punta Cana", region=self.region, pais_destino=self.pais,
            precio=Decimal("800"), duracion_noches=5, salidas="Quito",
            imagen_url="https://example.com/img.jpg", descripcion_corta="",
            tipo_paquete=self.tipo, temporada=self.temp, destacado=True, activo=True
        )
        self.p2 = PaqueteTuristico.objects.create(
            titulo="Samana", region=self.region, pais_destino=self.pais,
            precio=Decimal("400"), duracion_noches=3, salidas="Guayaquil",
            imagen_url="https://example.com/img.jpg", descripcion_corta="",
            activo=False
        )

    def test_solo_activos(self):
        qs = PaqueteTuristico.objects.filter(activo=True)
        self.assertEqual(qs.count(), 1)

    def test_filtro_por_tipo(self):
        qs = PaqueteTuristico.objects.filter(activo=True, tipo_paquete__nombre__iexact="Vacaciones")
        self.assertEqual(qs.count(), 1)

    def test_filtro_por_precio_max(self):
        qs = PaqueteTuristico.objects.filter(activo=True, precio__lte=Decimal("500"))
        self.assertEqual(qs.count(), 0)

    def test_filtro_destacados(self):
        qs = PaqueteTuristico.objects.filter(activo=True, destacado=True)
        self.assertEqual(qs.count(), 1)

    def test_filtro_por_temporada(self):
        qs = PaqueteTuristico.objects.filter(activo=True, temporada__nombre__iexact="Temporada Alta")
        self.assertEqual(qs.count(), 1)


class VueloViewSetFilterTest(TestCase):
    def setUp(self):
        self.region = Region.objects.create(nombre="sudamerica", orden=1)
        self.pais = PaisRegion.objects.create(region=self.region, nombre="Ecuador", codigo_iso="EC")
        self.ciudad = Ciudad.objects.create(pais=self.pais, nombre="Quito", codigo_ciudad="UIO")
        self.aerolinea = Aerolinea.objects.create(nombre="Latam", codigo_iata="LA")
        self.aeropuerto_uio = Aeropuerto.objects.create(
            codigo_iata="UIO", nombre="Mariscal Sucre", pais=self.pais, ciudad=self.ciudad
        )
        self.aeropuerto_gye = Aeropuerto.objects.create(
            codigo_iata="GYE", nombre="Jose Joaquin", pais=self.pais
        )

        self.v1 = Vuelo.objects.create(
            aerolinea=self.aerolinea, origen=self.aeropuerto_uio, destino=self.aeropuerto_gye,
            duracion="0h 45m", precio=Decimal("150"), disponible=True, destacado=True
        )

    def test_solo_disponibles(self):
        Vuelo.objects.create(
            aerolinea=self.aerolinea, origen=self.aeropuerto_uio, destino=self.aeropuerto_gye,
            duracion="0h 45m", precio=Decimal("100"), disponible=False
        )
        qs = Vuelo.objects.filter(disponible=True)
        self.assertEqual(qs.count(), 1)

    def test_filtro_por_origen(self):
        qs = Vuelo.objects.filter(
            disponible=True, origen__codigo_iata__icontains="UIO"
        )
        self.assertEqual(qs.count(), 1)


# ============================================================
# CHATBOT TESTS (mantener los originales)
# ============================================================

class BuildAccionTest(TestCase):
    def test_vuelos_live_retorna_accion_redirect(self):
        accion = _build_accion("buscar_vuelos_live", {
            "origen": "UIO", "destino": "MIA", "fecha_salida": "2025-08-15", "adultos": 2,
        })
        self.assertEqual(accion["tipo"], "redirect_vuelos")
        self.assertEqual(accion["path"], "/vuelos/resultados")
        self.assertEqual(accion["params"]["origin"], "UIO")
        self.assertEqual(accion["params"]["destination"], "MIA")
        self.assertEqual(accion["params"]["date"], "2025-08-15")
        self.assertEqual(accion["params"]["adults"], 2)
        self.assertIn("label", accion)

    def test_detalle_paquete_retorna_accion_redirect(self):
        accion = _build_accion("get_detalle_paquete", {"paquete_id": 42})
        self.assertEqual(accion["tipo"], "redirect_paquete")
        self.assertEqual(accion["path"], "/paquetes/42")
        self.assertEqual(accion["params"], {})
        self.assertIn("label", accion)

    def test_otras_tools_retornan_none(self):
        self.assertIsNone(_build_accion("get_paquetes", {}))
        self.assertIsNone(_build_accion("get_regiones", {}))
        self.assertIsNone(_build_accion("get_vuelos", {"origen": "UIO"}))
        self.assertIsNone(_build_accion("get_aerolineas", {}))

    def test_vuelos_con_fecha_regreso(self):
        accion = _build_accion("buscar_vuelos_live", {
            "origen": "GYE", "destino": "MAD", "fecha_salida": "2025-09-01",
            "adultos": 1, "fecha_regreso": "2025-09-15",
        })
        self.assertEqual(accion["params"]["return_date"], "2025-09-15")
        self.assertEqual(accion["params"]["tipoViaje"], "idaVuelta")

    def test_vuelos_sin_fecha_regreso_tipo_solo_ida(self):
        accion = _build_accion("buscar_vuelos_live", {
            "origen": "UIO", "destino": "MIA", "fecha_salida": "2025-08-15", "adultos": 1,
        })
        self.assertEqual(accion["params"].get("tipoViaje"), "soloIda")

    def test_detalle_paquete_sin_id_retorna_none(self):
        self.assertIsNone(_build_accion("get_detalle_paquete", {}))
        self.assertIsNone(_build_accion("get_detalle_paquete", {"paquete_id": 0}))


from unittest.mock import patch

class EjecutarToolTest(TestCase):
    def test_retorna_tupla_resultado_y_accion(self):
        resultado_json, accion = ejecutar_tool("get_aerolineas", {})
        self.assertIsInstance(resultado_json, str)
        self.assertIsNone(accion)

    def test_buscar_vuelos_live_retorna_accion(self):
        args = {"origen": "UIO", "destino": "MIA", "fecha_salida": "2025-08-15", "adultos": 1}
        with patch("servicios.chatbot.tool_buscar_vuelos_live", return_value=[]):
            resultado_json, accion = ejecutar_tool("buscar_vuelos_live", args)
        self.assertIsNotNone(accion)
        self.assertEqual(accion["tipo"], "redirect_vuelos")

    def test_get_detalle_paquete_retorna_accion(self):
        with patch("servicios.chatbot.tool_get_detalle_paquete", return_value={"id": 5}):
            resultado_json, accion = ejecutar_tool("get_detalle_paquete", {"paquete_id": 5})
        self.assertIsNotNone(accion)
        self.assertEqual(accion["tipo"], "redirect_paquete")


class ProcesarMensajeRetornaAccionTest(TestCase):
    @patch("servicios.chatbot.get_groq_client")
    def test_respuesta_sin_tools_tiene_accion_none(self, mock_client):
        mock_choice = MagicMock()
        mock_choice.message.tool_calls = None
        mock_choice.message.content = "Hola, soy Cory."
        mock_client.return_value.chat.completions.create.return_value.choices = [mock_choice]

        resultado = procesar_mensaje("Hola")
        self.assertIn("respuesta", resultado)
        self.assertIn("historial", resultado)
        self.assertIn("accion", resultado)
        self.assertIsNone(resultado["accion"])
