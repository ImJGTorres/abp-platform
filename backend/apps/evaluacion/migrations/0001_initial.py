import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Rubrica',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'db_table': 'rubrica',
            },
        ),
        migrations.CreateModel(
            name='CriterioRubrica',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('descripcion', models.TextField()),
                ('peso', models.DecimalField(decimal_places=2, max_digits=5)),
                ('id_rubrica', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='criterios',
                    to='evaluacion.rubrica',
                )),
            ],
            options={
                'db_table': 'criterio_rubrica',
            },
        ),
    ]
