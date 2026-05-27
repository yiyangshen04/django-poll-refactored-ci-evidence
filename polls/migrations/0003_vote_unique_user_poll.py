from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0002_auto_20231018_1318'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='vote',
            constraint=models.UniqueConstraint(
                fields=('user', 'poll'),
                name='one_vote_per_user_per_poll',
            ),
        ),
    ]
