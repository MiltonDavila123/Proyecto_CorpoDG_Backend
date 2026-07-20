# Crea el grupo "Asesor" con permisos operativos (reservas, clientes,
# solicitudes) sin acceso a la data maestra ni a la configuración.
# El rol "Admin" corresponde a los superusuarios de Django, que ven todo.
from django.db import migrations

ASESOR_GROUP = 'Asesor'

# (app_label, model, [permisos])
PERMISOS_ASESOR = [
    ('servicios', 'reservavuelo', ['view', 'change']),
    ('servicios', 'reservapaquete', ['view', 'change']),
    ('servicios', 'cliente', ['view', 'add', 'change']),
    ('servicios', 'solicitud', ['view', 'change']),
    ('servicios', 'destino', ['view']),
    ('servicios', 'vuelo', ['view']),
    ('servicios', 'paqueteturistico', ['view']),
]


def crear_grupo_asesor(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    grupo, _ = Group.objects.get_or_create(name=ASESOR_GROUP)

    for app_label, model, acciones in PERMISOS_ASESOR:
        ct, _ = ContentType.objects.get_or_create(
            app_label=app_label, model=model,
        )
        for accion in acciones:
            perm, _ = Permission.objects.get_or_create(
                codename=f'{accion}_{model}',
                content_type=ct,
                defaults={'name': f'Can {accion} {model}'},
            )
            grupo.permissions.add(perm)


def eliminar_grupo_asesor(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name=ASESOR_GROUP).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('servicios', '0024_reservavuelo_reservapaquete'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(crear_grupo_asesor, eliminar_grupo_asesor),
    ]
