from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from datetime import timedelta

# Model TransactionType là loại giao dịch (thu nhập, chi tiêu)
class TransactionType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# Model Category là danh mục của giao dịch (thu, chi)
class Category(models.Model):
    name = models.CharField(max_length=100)
    type = models.ForeignKey(TransactionType, on_delete=models.CASCADE) 
    icon = models.ImageField(upload_to='icons/', blank=True, null=True)

    def __str__(self):
        return self.name

# Model Transaction là giao dịch gồm các thông tin: người dùng, danh mục, số tiền, mô tả, ngày giao dịch
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    # amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.IntegerField()
    description = models.TextField(blank=True)
    transaction_date = models.DateTimeField()

    # def __str__(self):
    #     return f"{self.amount} - {self.category.name}"
    # nếu mà category có type là thu thì trả về số tiền dương con không thì trả về số tiền âm
    def get_amount(self):
        if self.category.type.name == 'Thu':
            # lấy amout là số dương nếu category là thu
            if self.amount > 0:
                return self.amount
            return -self.amount
        else:
            if self.amount < 0:
                return self.amount
            return -self.amount
    def save(self, *args, **kwargs):
        self.amount = self.get_amount()
        super(Transaction, self).save(*args, **kwargs)

# Model UserProfile là thông tin cá nhân của người dùng
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return self.user.username


class OTP(models.Model):
    email = models.EmailField(unique=True) 
    code = models.CharField(max_length=6)  
    created_at = models.DateTimeField(auto_now=True)  

    def is_valid(self):
        print("-----------------")
        print(self.created_at)
        print(self.created_at + timedelta(minutes=5))
        print(now())
        print("-----------------")
        return now() < self.created_at + timedelta(minutes=5)  


# Tự động tạo UserProfile khi tạo User
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()