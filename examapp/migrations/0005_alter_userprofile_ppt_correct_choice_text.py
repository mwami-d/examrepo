# Generated by Django 5.2.1 on 2025-05-21 15:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('examapp', '0004_userprofile_ppt_correct_choice_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='ppt_correct_choice_text',
            field=models.CharField(default='#000000', max_length=7),
        ),
    ]
