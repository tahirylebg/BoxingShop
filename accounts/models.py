from decimal import Decimal

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class CustomerManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra)


class Customer(AbstractUser):
    """Compte client. Identifiant de connexion : l'e-mail."""

    class ClubStatus(models.TextChoices):
        NONE = "none", "Particulier"
        PENDING = "pending", "Demande Club/Coach en attente"
        APPROVED = "approved", "Club/Coach validé"
        REJECTED = "rejected", "Demande refusée"

    username = None
    email = models.EmailField("e-mail", unique=True)
    phone = models.CharField("téléphone", max_length=30, blank=True)
    club_status = models.CharField(
        "statut Club/Coach", max_length=10, choices=ClubStatus.choices, default=ClubStatus.NONE, db_index=True
    )
    club_name = models.CharField("nom du club / de la structure", max_length=150, blank=True)
    club_siret = models.CharField("SIRET / n° d'affiliation", max_length=40, blank=True)
    club_message = models.TextField("message de la demande", blank=True)
    club_requested_at = models.DateTimeField("demande envoyée le", null=True, blank=True)
    club_validated_at = models.DateTimeField("validé le", null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomerManager()

    class Meta:
        verbose_name = "client"
        verbose_name_plural = "clients"

    def __str__(self):
        return self.get_full_name() or self.email

    @property
    def is_club(self):
        return self.club_status == self.ClubStatus.APPROVED

    def approve_club(self):
        self.club_status = self.ClubStatus.APPROVED
        self.club_validated_at = timezone.now()


class Address(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField("libellé", max_length=50, blank=True, help_text="Ex. Domicile, Club…")
    first_name = models.CharField("prénom", max_length=80)
    last_name = models.CharField("nom", max_length=80)
    line1 = models.CharField("adresse", max_length=200)
    line2 = models.CharField("complément", max_length=200, blank=True)
    postal_code = models.CharField("code postal", max_length=10)
    city = models.CharField("ville", max_length=100)
    country = models.CharField("pays", max_length=2, default="FR")
    phone = models.CharField("téléphone", max_length=30, blank=True)
    is_default = models.BooleanField("adresse par défaut", default=False)

    class Meta:
        verbose_name = "adresse"
        verbose_name_plural = "adresses"
        ordering = ["-is_default", "id"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}, {self.line1}, {self.postal_code} {self.city}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            Address.objects.filter(customer=self.customer).exclude(pk=self.pk).update(is_default=False)


class ClubPriceTier(models.Model):
    """Remise accordée aux comptes Club/Coach validés selon la quantité totale du panier."""

    min_quantity = models.PositiveIntegerField("à partir de (articles)", unique=True)
    discount_percent = models.DecimalField(
        "remise (%)",
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("60"))],
    )

    class Meta:
        verbose_name = "palier tarifaire club"
        verbose_name_plural = "grille tarifaire clubs"
        ordering = ["min_quantity"]

    def __str__(self):
        return f"≥ {self.min_quantity} articles : -{self.discount_percent} %"
