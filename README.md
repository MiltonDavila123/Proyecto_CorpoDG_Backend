# CorpoDG Backend — API de Viajes

Backend Django REST para **CorpoDG Trip593**. Proporciona API de catálogo turístico, búsqueda y reserva de vuelos con Sabre GDS, pagos con Stripe, chatbot IA (Groq) y panel admin.

**Stack:** Django 6.0.1 · Django REST Framework · PostgreSQL · python-decouple · Gunicorn

## Inicio rápido

```bash
git clone https://github.com/Gabriel2146/Proyecto_CorpoDG_Backend.git
cd Proyecto_CorpoDG_Backend
pip install -r requirements.txt
cp .env.example .env   # editar credenciales
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

## Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `SECRET_KEY` | Clave secreta Django |
| `DEBUG` | True/False |
| `ALLOWED_HOSTS` | Hosts permitidos (coma separado) |
| `CORS_ALLOWED_ORIGINS` | Orígenes CORS |
| `DB_ENGINE` | `django.db.backends.postgresql` o `sqlite3` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Base de datos |
| `CLIENT_ID`, `CLIENT_SECRET` | Credenciales Sabre GDS |
| `SABRE_AUTH_URL` | URL de autenticación Sabre |
| `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET` | Stripe |
| `GROQ_API_KEY` | API key para el chatbot Cory (Groq) |
| `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_TEMPLATE_NAME` | WhatsApp Cloud API |
| `EMAIL_HOST*` | Configuración SMTP |
| `FRONTEND_BOOKING_SUCCESS_URL`, `FRONTEND_BOOKING_CANCEL_URL` | URLs de retorno |
| `BOOKING_SANDBOX`, `SEATMAP_SANDBOX` | Modo sandbox Sabre |
| `AUTH_TOKEN` | Token opcional para endpoints protegidos |

## API Endpoints

### Catálogo (solo lectura pública)
| Endpoint | Descripción |
|----------|-------------|
| `GET /api/regiones/` | Regiones turísticas (10) con imágenes y orden |
| `GET /api/destinos/` | Destinos turísticos |
| `GET /api/paquetes/` | Paquetes turísticos con precios y detalles |
| `GET /api/paises-region/` | Países por región |
| `GET /api/ciudades/` | Ciudades |
| `GET /api/aerolineas/` | Aerolíneas con logos |
| `GET /api/aeropuertos/` | Aeropuertos |
| `GET /api/tipos-paquete/` | Tipos de paquete |
| `GET /api/temporadas/` | Temporadas |

### Gestión (CRUD autenticado)
| Endpoint | Descripción |
|----------|-------------|
| `GET/POST /api/clientes/` | Clientes |
| `GET/POST /api/solicitudes/` | Solicitudes de contacto |
| `GET/POST /api/vuelos/` | Vuelos guardados |

### Vuelos Sabre GDS
| Endpoint | Descripción |
|----------|-------------|
| `POST /api/buscar-vuelos-live/` | Búsqueda en vivo de vuelos |
| `POST /api/revalidar-vuelo/` | Revalidar precio/disponibilidad |
| `GET /api/seatmap/` | Mapa de asientos |
| `POST /api/booking/checkout/` | Crear sesión Stripe para vuelo |
| `POST /api/booking/confirm/` | Confirmar reserva Sabre + Stripe |
| `POST /api/booking/webhook/` | Webhook Stripe |
| `GET /api/booking/voucher/<uid>/` | Descargar voucher PDF |

### Paquetes turísticos
| Endpoint | Descripción |
|----------|-------------|
| `POST /api/paquetes/booking/checkout/` | Crear sesión Stripe para paquete |
| `POST /api/paquetes/booking/confirm/` | Confirmar reserva de paquete |
| `GET /api/paquetes/booking/voucher/<uid>/` | Descargar voucher PDF |

### Otros
| Endpoint | Descripción |
|----------|-------------|
| `POST /api/contacto/` | Formulario de contacto |
| `POST /api/chatbot/` | Chatbot Cory (Groq IA + function calling) |
| `GET /api/health/` | Health check |
| `GET /api/seed/` | Seed de datos de referencia |
| `GET /api/admin-ajax/*` | Endpoints AJAX para admin Django |

## Modelos principales

- `Region`, `PaisRegion`, `Ciudad` — Geografía turística
- `Destino`, `PaqueteTuristico` — Catálogo con precios, imágenes, itinerarios
- `Vuelo` — Vuelos guardados
- `Aerolinea`, `Aeropuerto` — Referencias
- `Cliente`, `Solicitud` — Clientes y solicitudes
- `TipoPaquete`, `Temporada`, `TipoViaje` — Clasificación
- `ConfiguracionDestacados`, `OrdenVueloDestacado`, `OrdenPaqueteDestacado`, `OrdenDestinoDestacado` — Orden de destacados

## Comandos de gestión

```bash
python manage.py seed_data          # Poblar base de datos con datos de referencia
python manage.py desactivar_paquetes_vencidos  # Desactivar paquetes caducados
```

## Tests

```bash
python manage.py test servicios
```

**78 tests unitarios** — modelos, vistas, y lógica de negocio.

## Integraciones

- **Sabre GDS** — búsqueda, revalidación, seatmap, reserva y emisión (sandbox/ producción vía `BOOKING_SANDBOX`)
- **Stripe** — checkout, webhooks, generación de vouchers PDF
- **Groq (Llama 3)** — chatbot Cory con function calling para consultar base de datos, Sabre y clima
- **WhatsApp Cloud API** — notificaciones al recibir solicitudes de contacto
- **xhtml2pdf** — generación de vouchers PDF con Google Drive preview

## CI/CD

- **GitHub Actions CI** — Python 3.13, PostgreSQL 17, 78 tests, ruff lint
- **Performance** — k6 con 3 endpoints (destinos, paquetes, vuelos live)
- **Render** — despliegue automático desde `staging`, PostgreSQL 15 free tier
