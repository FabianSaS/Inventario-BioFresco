from django.db import migrations

def crear_grupos(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    roles = ['Administrador', 'Bodeguero', 'Gerente']
    for rol in roles:
        Group.objects.get_or_create(name=rol)

def eliminar_grupos(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    roles = ['Administrador', 'Bodeguero', 'Gerente']
    Group.objects.filter(name__in=roles).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('bioapp', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_grupos, eliminar_grupos),
    ]