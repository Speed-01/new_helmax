from django import forms
from manager.models import Address

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['address_type', 'full_name', 'phone', 'pincode', 'address_line1', 'address_line2', 'landmark', 'city', 'state', 'is_default']
        widgets = {
            'address_type': forms.Select(attrs={'class': 'w-full bg-zinc-800 rounded px-4 py-2 text-white'}),
            'full_name': forms.TextInput(attrs={'class': 'w-full bg-zinc-800 rounded px-4 py-2 text-white placeholder-gray-400', 'placeholder': 'Name'}),
            'phone': forms.TextInput(attrs={'class': 'w-full bg-zinc-800 rounded px-4 py-2 text-white placeholder-gray-400', 'placeholder': 'Mobile'}),
            'pincode': forms.TextInput(attrs={'class': 'w-full bg-zinc-800 rounded px-4 py-2 text-white placeholder-gray-400', 'placeholder': 'Pincode'}),
            'address_line1': forms.TextInput(attrs={'class': 'w-full bg-zinc-800 rounded px-4 py-2 text-white placeholder-gray-400', 'placeholder': 'Address Line 1'}),
            'address_line2': forms.TextInput(attrs={'class': 'w-full bg-zinc-800 rounded px-4 py-2 text-white placeholder-gray-400', 'placeholder': 'Address Line 2'}),
            'landmark': forms.TextInput(attrs={'class': 'w-full bg-zinc-800 rounded px-4 py-2 text-white placeholder-gray-400', 'placeholder': 'Landmark'}),
            'city': forms.TextInput(attrs={'class': 'w-full bg-zinc-800 rounded px-4 py-2 text-white placeholder-gray-400', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'w-full bg-zinc-800 rounded px-4 py-2 text-white placeholder-gray-400', 'placeholder': 'State'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'rounded bg-zinc-800 text-orange-500 focus:ring-orange-500'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError("Please enter a valid 10-digit phone number.")
        return phone

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if not pincode.isdigit() or len(pincode) != 6:
            raise forms.ValidationError("Please enter a valid 6-digit pincode.")
        return pincode
