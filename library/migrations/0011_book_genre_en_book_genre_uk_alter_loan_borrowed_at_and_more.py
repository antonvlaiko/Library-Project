# Generated by Django 5.1.4 on 2025-06-08 08:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0010_loan_is_rejected_loan_rejected_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='genre_en',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Genre (English'),
        ),
        migrations.AddField(
            model_name='book',
            name='genre_uk',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Genre (Ukrainian'),
        ),
        migrations.AlterField(
            model_name='loan',
            name='borrowed_at',
            field=models.DateTimeField(verbose_name='Borrowed At'),
        ),
        migrations.AlterField(
            model_name='loan',
            name='due_date',
            field=models.DateTimeField(verbose_name='Due Date'),
        ),
    ]
