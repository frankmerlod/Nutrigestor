from django import forms
from .models import Usuario, AlimentoEnOpcion, OpcionMenu, Comida, Alimento

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'edad', 'peso', 'altura', 'sexo', 'nivel_actividad', 'cuello', 'cintura', 'caderas', 'objetivo_entrenamiento', 'objetivo_peso']

class ComidaForm(forms.ModelForm):
    class Meta:
        model = Comida
        fields = ['nombre', 'orden']
        
class OpcionMenuForm(forms.ModelForm):
    class Meta:
        model = OpcionMenu
        fields = ['nombre']

class AlimentoEnOpcionForm(forms.ModelForm):
    class Meta:
        model = AlimentoEnOpcion
        fields = ['alimento', 'cantidad', 'cantidad_unidades']
        
class AlimentoForm(forms.ModelForm):
    class Meta:
        model = Alimento
        fields = ['nombre', 'calorias', 'proteinas', 'carbohidratos', 'grasas', 'cantidad_gramos', 'cantidad_unidades', 'unidad', 'nutrientes', 'imagen']