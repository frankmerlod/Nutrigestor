from django.db import models
import math


class Usuario(models.Model):
    SEXO_OPCIONES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]

    ACTIVIDAD_OPCIONES = [
        (1.2, 'Sedentario'),
        (1.375, 'Ligero'),
        (1.55, 'Moderado'),
        (1.725, 'Activo'),
        (1.9, 'Muy activo'),
    ]
    
    OBJETIVO_ENTRENAMIENTO_OPCIONES = [
        ('Aumentar masa muscular', 'Aumentar masa muscular'),
        ('Mantener peso', 'Mantener peso'),
        ('Reducir porcentaje de grasa', 'Reducir porcentaje de grasa'),
    ]

    OBJETIVO_PESO_OPCIONES = [
        (1.1, '0.5 kg/semana'),
        (1.15, '3 kg/semana'),
        (1.2, '5 kg/semana'),
    ]

    nombre = models.CharField(max_length=90, blank=False, null=False)
    edad = models.IntegerField(default=18)
    peso = models.FloatField(default=50)  # en kilogramos
    altura = models.FloatField(default=150)  # en centímetros
    sexo = models.CharField(max_length=1, choices=SEXO_OPCIONES)
    nivel_actividad = models.FloatField(choices=ACTIVIDAD_OPCIONES, default=1.2)
    cuello = models.FloatField(default=30)  # en centímetros
    cintura = models.FloatField(default=60)  # en centímetros
    caderas = models.FloatField(default=90)  # en centímetros (solo para mujeres)
    objetivo_entrenamiento = models.CharField(max_length=30, choices=OBJETIVO_ENTRENAMIENTO_OPCIONES, default='Mantener peso')
    objetivo_peso = models.FloatField(choices=OBJETIVO_PESO_OPCIONES, null=True, blank=True)  # Solo para 'Aumentar masa muscular'
    macros_proteina = models.FloatField(default=21)
    macros_carbohidratos = models.FloatField(default=50)
    macros_grasas = models.FloatField(default=29)
    

    def __str__(self):
        return self.nombre

    def tasa_metabolica_basal(self):
        if self.sexo == 'M':
            tmb = 66 + (13.7 * self.peso) + (5 * self.altura) - (6.8 * self.edad)
        else:
            tmb = 655 + (9.6 * self.peso) + (1.8 * self.altura) - (4.7 * self.edad)
        return round(tmb,2)

    def porcentaje_grasa(self):
        # Fórmula simplificada para porcentaje de grasa corporal
        if self.sexo == 'M':
            grasa = 495 / ((1.0324 - 0.19077 * math.log10(self.cintura - self.cuello)) + 0.15456 * math.log10(self.altura)) - 450
        else:
            grasa = 495 / ((1.29579 - 0.35004 * math.log10(self.cintura + self.caderas - self.cuello)) + 0.22100 * math.log10(self.altura)) -450
        return round((grasa),2)

    def gasto_calorico(self):
        tmb = self.tasa_metabolica_basal()
        return round((tmb * self.nivel_actividad),2)

    def objetivo_calorias(self):
        mantener_peso_calorias = self.gasto_calorico()

        if self.objetivo_entrenamiento == 'Mantener peso':
            return round(mantener_peso_calorias,2)
        
        elif self.objetivo_entrenamiento == 'Aumentar masa muscular':
            if self.objetivo_peso:
                return round((mantener_peso_calorias * self.objetivo_peso),2)
            else:
                return round(mantener_peso_calorias,2)
            
        elif self.objetivo_entrenamiento == 'Reducir porcentaje de grasa':
            porcentaje_grasa = self.porcentaje_grasa()
            if porcentaje_grasa <= 17.4:
                return round((mantener_peso_calorias * 0.9),2)
            elif porcentaje_grasa <= 20.4:
                return round((mantener_peso_calorias * 0.84),2)
            elif porcentaje_grasa <= 24.4:
                return round((mantener_peso_calorias * 0.76),2)
            else:
                return round((mantener_peso_calorias * 0.7),2)
        else:
            return mantener_peso_calorias
        
        
    def porcentaje_macros(self):
        objetivo = self.objetivo_calorias()
        proteinas = objetivo * self.macros_proteina / 100
        proteinas = round((proteinas / 4),2)
        proteinasxkg = round((proteinas / self.peso),2)
        carbohidratos = objetivo * self.macros_carbohidratos / 100
        carbohidratos = round((carbohidratos / 4),2)
        carbohidratosxkg = round((carbohidratos / self.peso),2)
        grasas = objetivo * self.macros_grasas / 100
        grasas = round((grasas / 9),2)
        grasasxkg = round((grasas / self.peso),2)
        
        return (proteinas, proteinasxkg, carbohidratos, carbohidratosxkg, grasas, grasasxkg)
    
    #nueva funcion para % de calorias en cada comida
    def asignar_porcentaje_calorias(self):
        comidas = self.comida_set.all().order_by('orden')
        total_comidas = comidas.count()
        if total_comidas > 0:
            porcentaje_por_comida = round(100 / total_comidas, 2)
            for comida in comidas:
                comida.porcentaje_calorias = porcentaje_por_comida
                comida.save()

    def obtener_porcentajes_calorias(self):
        comidas = self.comida_set.all().order_by('orden')
        return [(comida.nombre, comida.porcentaje_calorias) for comida in comidas]
    
    
        
        
class Comida(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100, blank=False, null=False)
    orden = models.IntegerField()
    porcentaje_calorias = models.FloatField(default=0.0)  # Nuevo campo para el porcentaje de calorías
    
    
    #funcion para calcular macros de cada comida
    def calcular_macronutrientes(self):
        usuario = self.usuario
        calorias_totales = usuario.objetivo_calorias() #2300
        calorias_comida = (self.porcentaje_calorias * calorias_totales ) / 100 #si %calorias = 25 ==> 575
        
        
        proteinas_comida = (calorias_comida * (usuario.macros_proteina / 100)) / 4  #si kcalxcomida = 25%  y proteinaxcomida 28% ==> 40.25g
        carbohidratos_comida = (calorias_comida * (usuario.macros_carbohidratos / 100)) / 4
        grasas_comida = (calorias_comida * (usuario.macros_grasas / 100)) / 9
        
        return {
            'calorias_por_comida': round(calorias_comida, 2),
            'proteinas_por_comida': round(proteinas_comida, 2),
            'carbohidratos_por_comida': round(carbohidratos_comida, 2),
            'grasas_por_comida': round(grasas_comida, 2)
        }
        
    def __str__(self):
        return self.nombre

class OpcionMenu(models.Model):
    comida = models.ForeignKey(Comida, on_delete=models.CASCADE, related_name='opciones_menu')
    nombre = models.CharField(max_length=100, blank=False, null=False, default='Opción sin nombre')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre
    
    def total_calorias(self):
        return round((sum(alimento.calorias for alimento in self.alimentos_en_opcion.all())),2)

    def total_proteinas(self):
        return round((sum(alimento.proteinas for alimento in self.alimentos_en_opcion.all())),2)

    def total_carbohidratos(self):
        return round((sum(alimento.carbohidratos for alimento in self.alimentos_en_opcion.all())),2)

    def total_grasas(self):
        return round((sum(alimento.grasas for alimento in self.alimentos_en_opcion.all())),2)

class Alimento(models.Model):
    nombre = models.CharField(max_length=100)
    calorias = models.FloatField(default=0)
    proteinas = models.FloatField(default=0)
    carbohidratos = models.FloatField(default=0)
    grasas = models.FloatField(default=0)
    #nuevos campos para guardar alimento
    cantidad_gramos = models.FloatField(default=0)
    cantidad_unidades = models.FloatField(default=0)
    unidad = models.CharField(max_length=20, default='Rebanadas/porciones/Tazas')
    imagen = models.ImageField(upload_to='alimentos/', null=True, blank=True)
    nutrientes = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return self.nombre
    
class AlimentoEnOpcion(models.Model):
    opcion_menu = models.ForeignKey(OpcionMenu, on_delete=models.CASCADE, related_name='alimentos_en_opcion')
    alimento = models.ForeignKey(Alimento, on_delete=models.CASCADE)
    cantidad = models.FloatField()  # Cantidad en gramos
    #nuevos campos para guardar alimento
    cantidad_unidades = models.FloatField(default=0)
    

    @property
    def calorias(self):
        cantidad_original = self.alimento.cantidad_gramos
        cantidad_nueva = self.cantidad
        unidades_original = self.alimento.cantidad_unidades
        unidades_nueva = self.cantidad_unidades
        calorias = self.alimento.calorias
        #Si la cantidad nueva diferente de cantidad original
        if cantidad_nueva != cantidad_original:
            return round(((cantidad_nueva * calorias) / cantidad_original),2)
        #Si la cantidad en unid nueva diferente de cantidad en unid orignal
        elif unidades_nueva != unidades_original:
            return round(((unidades_nueva * calorias) / unidades_original),2)
        else:
            return round(calorias,2)

    @property
    def proteinas(self):
        cantidad_original = self.alimento.cantidad_gramos
        cantidad_nueva = self.cantidad
        unidades_original = self.alimento.cantidad_unidades
        unidades_nueva = self.cantidad_unidades
        proteinas = self.alimento.proteinas
        #Si la cantidad nueva diferente de cantidad original
        if cantidad_nueva != cantidad_original:
            return round(((cantidad_nueva * proteinas) / cantidad_original),2)
        #Si la cantidad en unid nueva diferente de cantidad en unid orignal
        elif unidades_nueva != unidades_original:
            return round(((unidades_nueva * proteinas) / unidades_original),2)
        else:
            return round(proteinas,2)

    @property
    def carbohidratos(self):
        cantidad_original = self.alimento.cantidad_gramos
        cantidad_nueva = self.cantidad
        unidades_original = self.alimento.cantidad_unidades
        unidades_nueva = self.cantidad_unidades
        carbohidratos = self.alimento.carbohidratos
        #Si la cantidad nueva diferente de cantidad original
        if cantidad_nueva != cantidad_original:
            return round(((cantidad_nueva * carbohidratos) / cantidad_original),2)
        #Si la cantidad en unid nueva diferente de cantidad en unid orignal
        elif unidades_nueva != unidades_original:
            return round(((unidades_nueva * carbohidratos) / unidades_original),2)
        else:
            return round(carbohidratos,2)

    @property
    def grasas(self):
        cantidad_original = self.alimento.cantidad_gramos
        cantidad_nueva = self.cantidad
        unidades_original = self.alimento.cantidad_unidades
        unidades_nueva = self.cantidad_unidades
        grasas = self.alimento.grasas
        #Si la cantidad nueva diferente de cantidad original
        if cantidad_nueva != cantidad_original:
            return round(((cantidad_nueva * grasas) / cantidad_original),2)
        #Si la cantidad en unid nueva diferente de cantidad en unid orignal
        elif unidades_nueva != unidades_original:
            return round(((unidades_nueva * grasas) / unidades_original),2)
        else:
            return round(grasas,2)
    
    @property
    def unidad(self):
        return self.alimento.unidad
        