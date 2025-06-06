from django.shortcuts import render, redirect, get_object_or_404
from .models import Usuario, Comida, OpcionMenu, AlimentoEnOpcion, Alimento
from .forms import UsuarioForm, AlimentoEnOpcionForm, OpcionMenuForm, ComidaForm, AlimentoForm
from .utils import obtener_datos_alimentos
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
import requests
import json
from django.template.loader import render_to_string
from xhtml2pdf import pisa

# Create your views here.

#vista de usuario  
def lista_usuarios(request):
    usuarios = Usuario.objects.all()
    return render(request, 'gestor/lista_usuarios.html', {'usuarios': usuarios})

#agregar nuevo usuario
def agregar_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_usuarios')
    else:
        form = UsuarioForm()
    return render(request, 'gestor/agregar_usuario.html', {'form': form})

#edicion de usuario
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('detalle_usuario', args=[usuario.id]))
    else:
        form = UsuarioForm(instance=usuario)
    return render(request, 'gestor/editar_usuario.html', {'form': form, 'usuario': usuario})

def eliminar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        usuario.delete()
        return redirect('lista_usuarios')
    return render(request, 'gestor/eliminar_usuario.html', {'usuario': usuario})

#vista de detalles del usuario
def detalle_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    comidas = Comida.objects.filter(usuario=usuario).order_by('orden')
    return render(request, 'gestor/detalle_usuario.html', {'usuario': usuario, 'comidas': comidas})



#Vista de detalles del plan de alimentacion
def vista_nutricion(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    comidas = Comida.objects.filter(usuario=usuario).order_by('orden')
    # Calcular totales y porcentajes
    calorias_objetivo = usuario.objetivo_calorias()
    proteinas, proteinasxkg, carbohidratos, carbohidratosxkg, grasas, grasasxkgs = usuario.porcentaje_macros()

    # Procesar el formulario si se envía
    if request.method == 'POST':
        # Guardar porcentajes de macros
        usuario.macros_proteina = float(request.POST.get('macros_proteina'))
        usuario.macros_carbohidratos = float(request.POST.get('macros_carbohidratos'))
        usuario.macros_grasas = float(request.POST.get('macros_grasas'))
        usuario.save()

        # Guardar porcentajes de calorías por comida
        for comida in comidas:
            porcentaje = request.POST.get(f'porcentaje_{comida.id}')
            if porcentaje is not None:
                comida.porcentaje_calorias = float(porcentaje)
                comida.save()

        # Actualizar los cálculos después de guardar
        proteinas, proteinasxkg, carbohidratos, carbohidratosxkg, grasas, grasasxkgs = usuario.porcentaje_macros()

    # Preparar los datos de cada comida para la plantilla
    comidas_macronutrientes = [
        {
            'id': comida.id,
            'nombre': comida.nombre,
            'calorias_por_comida': comida.calcular_macronutrientes()['calorias_por_comida'],
            'proteinas_por_comida': comida.calcular_macronutrientes()['proteinas_por_comida'],
            'carbohidratos_por_comida': comida.calcular_macronutrientes()['carbohidratos_por_comida'],
            'grasas_por_comida': comida.calcular_macronutrientes()['grasas_por_comida'],
            'porcentaje_calorias': comida.porcentaje_calorias,
            'opciones_menu': comida.opciones_menu.all()
        }
        for comida in comidas
    ]

    # Preparar porcentajes de calorías para mostrar
    porcentajes_calorias = {comida.nombre: comida.porcentaje_calorias for comida in comidas}
    
    opciones_menu = [
        {
            'nombre': comida.nombre,
            'opciones': comida.opciones_menu.all()
        }
        for comida in comidas
    ]
    
    comidas_promedio = []
    
    for item in opciones_menu:
        nombre = item['nombre']
        total_calorias = 0
        total_proteinas = 0
        total_carbohidratos = 0
        total_grasas = 0
        count = 0   
        for opcion in item['opciones']:
            total_calorias += opcion.total_calorias()
            total_proteinas += opcion.total_proteinas()
            total_carbohidratos += opcion.total_carbohidratos()
            total_grasas += opcion.total_grasas()
            count += 1
        if count > 0:
            promedio_calorias = round((total_calorias / count),2)
            promedio_proteinas = round((total_proteinas / count),2)
            promedio_carbohidratos = round((total_carbohidratos / count),2)
            promedio_grasas = round((total_grasas / count),2)
        else:
            promedio_calorias = promedio_proteinas = promedio_carbohidratos = promedio_grasas = 0
            
        comidas_promedio.append({
            'nombre': nombre,
            'promedio_calorias': promedio_calorias,
            'promedio_proteinas': promedio_proteinas,
            'promedio_carbohidratos': promedio_carbohidratos,
            'promedio_grasas': promedio_grasas,
        })
    
    context = {
        'usuario': usuario,
        'calorias_objetivo': calorias_objetivo,
        'objetivo_entrenamiento': usuario.objetivo_entrenamiento,
        'macros_proteina': usuario.macros_proteina,
        'macros_carbohidratos': usuario.macros_carbohidratos,
        'macros_grasas': usuario.macros_grasas,
        'proteinas': proteinas,
        'carbohidratos': carbohidratos,
        'grasas': grasas,
        'protxkg' : proteinasxkg,
        'carbxkg' : carbohidratosxkg,
        'grasxkg' : grasasxkgs,
        'comidas': comidas_macronutrientes,
        'porcentajes_calorias': porcentajes_calorias,
        'comidas_promedio': comidas_promedio,
    }

    return render(request, 'gestor/vista_nutricion.html', context)

#Vista de detalle de comida
def detalle_comida(request, pk):
    comida = get_object_or_404(Comida, pk=pk)
    usuario = comida.usuario
    opciones_menu = comida.opciones_menu.all()
    comidas = Comida.objects.filter(usuario=usuario).order_by('orden')
    
    
    siguiente_comida = comida
    for index, c in enumerate(comidas):
        if c.id == comida.id:
            if index + 1 < len(comidas):
                siguiente_comida = comidas[index + 1]
            elif index == len(comidas) - 1 and index > 0:
                siguiente_comida = comidas[0]
            break

    # Guardar porcentajes de calorías por comida
    porcentaje = request.POST.get(f'porcentaje_{comida.id}')
    if porcentaje is not None:
        comida.porcentaje_calorias = float(porcentaje)
        comida.save()
    
    # Calcular totales y porcentajes
    calorias_objetivo = usuario.objetivo_calorias()
    proteinas, proteinasxkg, carbohidratos, carbohidratosxkg, grasas, grasasxkgs = usuario.porcentaje_macros()
    
    # Preparar los datos de cada comida para la plantilla
    comidas_macronutrientes = [
        {
            'id': comida.id,
            'nombre': comida.nombre,
            'calorias_por_comida': comida.calcular_macronutrientes()['calorias_por_comida'],
            'proteinas_por_comida': comida.calcular_macronutrientes()['proteinas_por_comida'],
            'carbohidratos_por_comida': comida.calcular_macronutrientes()['carbohidratos_por_comida'],
            'grasas_por_comida': comida.calcular_macronutrientes()['grasas_por_comida'],
            'porcentaje_calorias': comida.porcentaje_calorias,
            'opciones_menu': comida.opciones_menu.all(),
        } 
    ]
    
    porcentajes_calorias = comida.porcentaje_calorias
    
    total_calorias = 0
    total_proteinas = 0
    total_carbohidratos = 0
    total_grasas = 0
    count =0 
    
    for opcion in opciones_menu:
        suma = opcion.total_calorias()
        total_calorias += suma
        suma = opcion.total_proteinas()
        total_proteinas += suma
        suma = opcion.total_carbohidratos()
        total_carbohidratos += suma
        suma = opcion.total_grasas()
        total_grasas += suma
        count += 1
    
    if count > 0:
        promedio_calorias = round((total_calorias / count),2)
        promedio_proteinas = round((total_proteinas / count),2)
        promedio_carbohidratos = round((total_carbohidratos / count),2)
        promedio_grasas = round((total_grasas / count),2)
    else:
        promedio_calorias = promedio_proteinas = promedio_carbohidratos = promedio_grasas = 0
    
    
    context = {
        'usuario': usuario,
        'calorias_objetivo': calorias_objetivo,
        'objetivo_entrenamiento': usuario.objetivo_entrenamiento,
        'macros_proteina': usuario.macros_proteina,
        'macros_carbohidratos': usuario.macros_carbohidratos,
        'macros_grasas': usuario.macros_grasas,
        'proteinas': proteinas,
        'carbohidratos': carbohidratos,
        'grasas': grasas,
        'protxkg' : proteinasxkg,
        'carbxkg' : carbohidratosxkg,
        'grasxkg' : grasasxkgs,
        'comidas': comidas_macronutrientes,
        'porcentajes_calorias': porcentajes_calorias,
        'opciones_menu': opciones_menu,
        'siguiente_comida': siguiente_comida,
        'promedio_calorias': promedio_calorias,
        'promedio_proteinas': promedio_proteinas,
        'promedio_carbohidratos': promedio_carbohidratos,
        'promedio_grasas': promedio_grasas,
    }
    
    return render(request, 'gestor/detalle_comida.html', context)

#Vista para detalles de opcion
def detalle_opcion(request, opcion_id):
    opcion = get_object_or_404(OpcionMenu, pk=opcion_id)
    comida = opcion.comida
    usuario = comida.usuario
    comidas = Comida.objects.filter(usuario=usuario).order_by('orden')
    opciones_menu = OpcionMenu.objects.filter(comida=comida).order_by('id')

    siguiente_opcion = opcion
    for index, c in enumerate(opciones_menu):
        if c.id == opcion.id:
            if index + 1 < len(opciones_menu):
                siguiente_opcion = opciones_menu[index + 1]
            elif index == len(opciones_menu) - 1 and index > 0:
                siguiente_opcion = opciones_menu[0]
            break
        
    # Guardar porcentajes de calorías por comida
    porcentaje = request.POST.get(f'porcentaje_{comida.id}')
    if porcentaje is not None:
        comida.porcentaje_calorias = float(porcentaje)
        comida.save()
        
    # Preparar los datos de cada comida para la plantilla
    comidas_macronutrientes = [
        {
            'id': comida.id,
            'nombre': comida.nombre,
            'calorias_por_comida': comida.calcular_macronutrientes()['calorias_por_comida'],
            'proteinas_por_comida': comida.calcular_macronutrientes()['proteinas_por_comida'],
            'carbohidratos_por_comida': comida.calcular_macronutrientes()['carbohidratos_por_comida'],
            'grasas_por_comida': comida.calcular_macronutrientes()['grasas_por_comida'],
            'porcentaje_calorias': comida.porcentaje_calorias,
            'opciones_menu': comida.opciones_menu.all(),
            
        } 
    ]
    
    porcentajes_calorias = comida.porcentaje_calorias

    contexto = {
        'comida': comida,
        'usuario': usuario,
        'comidas': comidas,
        'opciones_menu': opciones_menu,
        'siguiente_opcion': siguiente_opcion,
        'opcion': opcion,
        'porcentajes_calorias': porcentajes_calorias,
        'comidas': comidas_macronutrientes,
    }
    return render(request, 'gestor/detalle_opcion.html', contexto)

#Nueva comida: desayuno almuerzo cena merienda
def agregar_comida(request, usuario_id):
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    if request.method == 'POST':
        form = ComidaForm(request.POST)
        if form.is_valid():
            comida = form.save(commit=False)
            comida.usuario = usuario
            comida.save()
            return redirect('vista_nutricion', pk=usuario.id)
    else:
        form = ComidaForm()
    return render(request, 'gestor/agregar_comida.html', {'form': form, 'usuario': usuario})

#Editar comidas existentes
def editar_comida(request, pk):
    comida = get_object_or_404(Comida, pk=pk)
    usuario = comida.usuario
    if request.method == 'POST':
        form = ComidaForm(request.POST, instance=comida)
        if form.is_valid():
            form.save()
            return redirect('vista_nutricion', pk=usuario.id)
    else:
        form = ComidaForm(instance=comida)
    return render(request, 'gestor/editar_comida.html', {'form': form, 'usuario': usuario, 'comida': comida})

#Eliminar comida existente
def eliminar_comida(request, pk):
    comida = get_object_or_404(Comida, pk=pk)
    usuario_id = comida.usuario.id
    if request.method == 'POST':
        comida.delete()
        return redirect('vista_nutricion', pk=usuario_id)
    return render(request, 'gestor/eliminar_comida.html', {'comida': comida})


#Agregar opciones dentro de una comida: opcion1 opcion2
# def agregar_opcion_menu(request, comida_id):
#     comida = get_object_or_404(Comida, pk=comida_id)
#     usuario = comida.usuario
#     if request.method == 'POST':
#         form = OpcionMenuForm(request.POST)
#         if form.is_valid():
#             opcion_menu = form.save(commit=False)
#             opcion_menu.usuario = usuario
#             opcion_menu.comida = comida
#             opcion_menu.save()
#             return redirect('vista_nutricion', pk=comida.usuario.pk)
#     else:
#         form = OpcionMenuForm()
#     return render(request, 'gestor/agregar_opcion_menu.html', {'form': form, 'comida': comida})

def agregar_opcion_menu(request, comida_id):
    comida = get_object_or_404(Comida, pk=comida_id)
    usuario = comida.usuario

    if request.method == 'POST':
        form = OpcionMenuForm(request.POST)
        if form.is_valid():
            nueva_opcion_menu = form.save(commit=False)
            nueva_opcion_menu.usuario = usuario
            nueva_opcion_menu.comida = comida
            nueva_opcion_menu.save()
            return redirect('detalle_comida', pk=comida.id)
    else:
        form = OpcionMenuForm()
    
    opciones_existentes = OpcionMenu.objects.all()

    return render(request, 'gestor/agregar_opcion_menu.html', {
        'form': form, 
        'comida': comida,
        'opciones_existentes': opciones_existentes,
    })

def agregar_opcion_menu_detalle(request, comida_id):
    comida = get_object_or_404(Comida, pk=comida_id)
    usuario = comida.usuario

    if request.method == 'POST':
        form = OpcionMenuForm(request.POST)
        if form.is_valid():
            nueva_opcion_menu = form.save(commit=False)
            nueva_opcion_menu.usuario = usuario
            nueva_opcion_menu.comida = comida
            nueva_opcion_menu.save()
            return redirect('detalle_comida', pk=comida.id)
    else:
        form = OpcionMenuForm()
    
    opciones_existentes = OpcionMenu.objects.all()

    return render(request, 'gestor/agregar_opcion_menu_detalle.html', {
        'form': form, 
        'comida': comida,
        'opciones_existentes': opciones_existentes,
    })

def copiar_opcion_menu(request, opcion_id, comida_id):
    opcion_existente = get_object_or_404(OpcionMenu, pk=opcion_id)
    comida = get_object_or_404(Comida, pk=comida_id)
    usuario = comida.usuario

    nueva_opcion_menu = OpcionMenu.objects.create(
        nombre=opcion_existente.nombre,
        usuario=usuario,
        comida=comida,
    )
    
    # Copiar los alimentos de la opción existente a la nueva opción
    for alimento_en_opcion in opcion_existente.alimentos_en_opcion.all():
        AlimentoEnOpcion.objects.create(
            opcion_menu=nueva_opcion_menu,
            alimento=alimento_en_opcion.alimento,
            cantidad=alimento_en_opcion.cantidad,
            cantidad_unidades=alimento_en_opcion.cantidad_unidades,
        )

    return JsonResponse({'success': True})


# Vista para editar una opción de menú existente
def editar_opcion_menu(request, pk):
    opcion_menu = get_object_or_404(OpcionMenu, pk=pk)
    comida = opcion_menu.comida
    if request.method == 'POST':
        form = OpcionMenuForm(request.POST, instance=opcion_menu)
        if form.is_valid():
            form.save()
            return redirect('vista_nutricion', pk=comida.usuario.id)
    else:
        form = OpcionMenuForm(instance=opcion_menu)
    return render(request, 'gestor/editar_opcion_menu.html', {'form': form, 'comida': comida, 'opcion_menu': opcion_menu})

def editar_opcion_menu_detalle(request, pk):
    opcion_menu = get_object_or_404(OpcionMenu, pk=pk)
    comida = opcion_menu.comida
    if request.method == 'POST':
        form = OpcionMenuForm(request.POST, instance=opcion_menu)
        if form.is_valid():
            form.save()
            return redirect('detalle_comida', pk=opcion_menu.comida.id)
    else:
        form = OpcionMenuForm(instance=opcion_menu)
    return render(request, 'gestor/editar_opcion_menu_detalle.html', {'form': form, 'comida': comida, 'opcion_menu': opcion_menu})

# Vista para eliminar una opción de menú existente
def eliminar_opcion_menu(request, pk):
    opcion_menu = get_object_or_404(OpcionMenu, pk=pk)
    usuario_id = opcion_menu.comida.usuario.id
    if request.method == 'POST':
        opcion_menu.delete()
        return redirect('vista_nutricion', pk=usuario_id)
    return render(request, 'gestor/eliminar_opcion_menu.html', {'opcion_menu': opcion_menu})

def eliminar_opcion_menu_detalle(request, pk):
    opcion_menu = get_object_or_404(OpcionMenu, pk=pk)
    usuario_id = opcion_menu.comida.usuario.id
    if request.method == 'POST':
        opcion_menu.delete()
        return redirect('detalle_comida', pk=opcion_menu.comida.id)
    return render(request, 'gestor/eliminar_opcion_menu_detalle.html', {'opcion_menu': opcion_menu})


#Agregar alimentos a opciones de comida
def agregar_alimento_en_opcion(request, opcion_id, usuario_id):
    opcion = get_object_or_404(OpcionMenu, pk=opcion_id, usuario__id=usuario_id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        calorias = request.POST.get('calorias')
        proteinas = request.POST.get('proteinas')
        carbohidratos = request.POST.get('carbohidratos')
        grasas = request.POST.get('grasas')
        cantidad = request.POST.get('cantidad')
        cantidad_unidades = request.POST.get('cantidadQty')
        unidad = request.POST.get('cantidadUnit')
        
        # Crear o obtener el alimento
        alimento, created = Alimento.objects.get_or_create(
            nombre=nombre,
            defaults={
                'calorias': calorias,
                'proteinas': proteinas,
                'carbohidratos': carbohidratos,
                'grasas': grasas,
                'cantidad_gramos': cantidad,
                'cantidad_unidades': cantidad_unidades,
                'unidad': unidad,
            }
        )
        
        # Asociar el alimento con la opción de menú
        alimento_en_opcion = AlimentoEnOpcion.objects.create(opcion_menu=opcion, alimento=alimento, cantidad=cantidad, cantidad_unidades=cantidad_unidades)
        
        return redirect('editar_alimento_en_opcion', opcion_id=alimento_en_opcion.id)

    return render(request, 'gestor/agregar_alimento_en_opcion.html', {'opcion': opcion})

# Agregar alimento en opcion desde la vista de detalle
def agregar_alimento_en_opcion_detalle(request, usuario_id, opcion_id ):
    opcion = get_object_or_404(OpcionMenu, pk=opcion_id, usuario__id=usuario_id)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        calorias = request.POST.get('calorias')
        proteinas = request.POST.get('proteinas')
        carbohidratos = request.POST.get('carbohidratos')
        grasas = request.POST.get('grasas')
        cantidad = request.POST.get('cantidad')
        cantidad_unidades = request.POST.get('cantidadQty')
        unidad = request.POST.get('cantidadUnit')
        
        # Crear o obtener el alimento
        alimento, created = Alimento.objects.get_or_create(
            nombre=nombre,
            defaults={
                'calorias': calorias,
                'proteinas': proteinas,
                'carbohidratos': carbohidratos,
                'grasas': grasas,
                'cantidad_gramos': cantidad,
                'cantidad_unidades': cantidad_unidades,
                'unidad': unidad,
            }
        )
        
        # Asociar el alimento con la opción de menú
        alimento_en_opcion = AlimentoEnOpcion.objects.create(opcion_menu=opcion, alimento=alimento, cantidad=cantidad, cantidad_unidades=cantidad_unidades)
        
        return redirect('editar_alimento_en_opcion_detalle', opcion_id=alimento_en_opcion.id)

    return render(request, 'gestor/agregar_alimento_en_opcion_detalle.html', {'usuario_id': usuario_id, 'opcion': opcion})

def agregar_alimento_en_opcion_detalle_opcion(request, usuario_id, opcion_id):
    opcion = get_object_or_404(OpcionMenu, pk=opcion_id, usuario__id=usuario_id)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        calorias = request.POST.get('calorias')
        proteinas = request.POST.get('proteinas')
        carbohidratos = request.POST.get('carbohidratos')
        grasas = request.POST.get('grasas')
        cantidad = request.POST.get('cantidad')
        cantidad_unidades = request.POST.get('cantidadQty')
        unidad = request.POST.get('cantidadUnit')
        
        # Crear o obtener el alimento
        alimento, created = Alimento.objects.get_or_create(
            nombre=nombre,
            defaults={
                'calorias': calorias,
                'proteinas': proteinas,
                'carbohidratos': carbohidratos,
                'grasas': grasas,
                'cantidad_gramos': cantidad,
                'cantidad_unidades': cantidad_unidades,
                'unidad': unidad,
            }
        )
        
        # Asociar el alimento con la opción de menú
        alimento_en_opcion = AlimentoEnOpcion.objects.create(opcion_menu=opcion, alimento=alimento, cantidad=cantidad, cantidad_unidades=cantidad_unidades)
        
        return redirect('editar_alimento_en_opcion_detalle_opcion', pk=alimento_en_opcion.id)

    return render(request, 'gestor/agregar_alimento_en_opcion_detalle_opcion.html', {'usuario_id': usuario_id, 'opcion': opcion})


#Editar alimento en opcion de comida
def editar_alimento_en_opcion(request, opcion_id):
    alimento_en_opcion = get_object_or_404(AlimentoEnOpcion, pk=opcion_id)

    if request.method == 'POST':
        cantidad = float(request.POST.get('cantidad', alimento_en_opcion.cantidad))
        cantidad_unidades = float(request.POST.get('cantidad_unidades', alimento_en_opcion.cantidad_unidades))

        if request.method == 'POST':
            cantidad = float(request.POST.get('cantidad'))
            cantidad_unidades = float(request.POST.get('cantidad_unidades'))

            alimento_en_opcion.cantidad = cantidad
            alimento_en_opcion.cantidad_unidades = cantidad_unidades
            alimento_en_opcion.save()

        return redirect('detalle_comida', pk=alimento_en_opcion.opcion_menu.comida.id)

    return render(request, 'gestor/editar_alimento_en_opcion.html', {
        'alimento_en_opcion': alimento_en_opcion,
        'calorias': alimento_en_opcion.calorias,
        'proteinas': alimento_en_opcion.proteinas,
        'carbohidratos': alimento_en_opcion.carbohidratos,
        'grasas': alimento_en_opcion.grasas,
        'unidad': alimento_en_opcion.unidad,
    })
    

#Editar alimento en opcion de comida en la vista de detalles de comida
def editar_alimento_en_opcion_detalle(request, opcion_id):
    alimento_en_opcion = get_object_or_404(AlimentoEnOpcion, pk=opcion_id)

    if request.method == 'POST':
        cantidad = float(request.POST.get('cantidad', alimento_en_opcion.cantidad))
        cantidad_unidades = float(request.POST.get('cantidad_unidades', alimento_en_opcion.cantidad_unidades))

        if request.method == 'POST':
            cantidad = float(request.POST.get('cantidad'))
            cantidad_unidades = float(request.POST.get('cantidad_unidades'))

            alimento_en_opcion.cantidad = cantidad
            alimento_en_opcion.cantidad_unidades = cantidad_unidades
            alimento_en_opcion.save()
            
        return redirect('detalle_comida', pk=alimento_en_opcion.opcion_menu.comida.id)

    return render(request, 'gestor/editar_alimento_en_opcion_detalle.html', {
        'alimento_en_opcion': alimento_en_opcion,
        'calorias': alimento_en_opcion.calorias,
        'proteinas': alimento_en_opcion.proteinas,
        'carbohidratos': alimento_en_opcion.carbohidratos,
        'grasas': alimento_en_opcion.grasas,
        'unidad': alimento_en_opcion.unidad,
    })
    
#Editar alimento en opcion de comida en la vista de detalles de la opcion
def editar_alimento_en_opcion_detalle_opcion(request, pk):
    alimento_en_opcion = get_object_or_404(AlimentoEnOpcion, pk=pk)

    if request.method == 'POST':
        cantidad = float(request.POST.get('cantidad', alimento_en_opcion.cantidad))
        cantidad_unidades = float(request.POST.get('cantidad_unidades', alimento_en_opcion.cantidad_unidades))

        if request.method == 'POST':
            cantidad = float(request.POST.get('cantidad'))
            cantidad_unidades = float(request.POST.get('cantidad_unidades'))

            alimento_en_opcion.cantidad = cantidad
            alimento_en_opcion.cantidad_unidades = cantidad_unidades
            alimento_en_opcion.save()

        return redirect('detalle_opcion', opcion_id=alimento_en_opcion.opcion_menu.id)  # Corregido aquí

    return render(request, 'gestor/editar_alimento_en_opcion_detalle_opcion.html', {
        'alimento_en_opcion': alimento_en_opcion,
        'calorias': alimento_en_opcion.calorias,
        'proteinas': alimento_en_opcion.proteinas,
        'carbohidratos': alimento_en_opcion.carbohidratos,
        'grasas': alimento_en_opcion.grasas,
        'unidad': alimento_en_opcion.unidad,
    })

#Eliminar alimento en opcion de comida
def eliminar_alimento_en_opcion(request, pk):
    alimento_en_opcion = get_object_or_404(AlimentoEnOpcion, pk=pk)
    usuario_pk = alimento_en_opcion.opcion_menu.comida.usuario.pk
    alimento_en_opcion.delete()
    return redirect('vista_nutricion', pk=usuario_pk)

#Eliminar alimento en opcion de comida en la vista de detalle de comida
def eliminar_alimento_en_opcion_detalle(request, pk):
    alimento_en_opcion = get_object_or_404(AlimentoEnOpcion, pk=pk)
    usuario_pk = alimento_en_opcion.opcion_menu.comida.usuario.pk
    alimento_en_opcion.delete()
    return redirect('detalle_comida', pk=alimento_en_opcion.opcion_menu.comida.id)

#Eliminar alimento en opcion de comida en la vista de detalle de opcion
def eliminar_alimento_en_opcion_detalle_opcion(request, pk):
    alimento_en_opcion = get_object_or_404(AlimentoEnOpcion, pk=pk)
    opcion_id = alimento_en_opcion.opcion_menu.id
    alimento_en_opcion.delete()
    return redirect('detalle_opcion', opcion_id=opcion_id)


#Vista de alimentos en base de datos
def lista_alimentos(request):
    alimentos = Alimento.objects.all()
    return render(request, 'gestor/lista_alimentos.html', {'alimentos': alimentos})

#Agregar nuevo alimento en base de datos
def agregar_alimento(request, opcion_id):
    opcion = get_object_or_404(OpcionMenu, pk=opcion_id)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        calorias = request.POST.get('calorias')
        proteinas = request.POST.get('proteinas')
        carbohidratos = request.POST.get('carbohidratos')
        grasas = request.POST.get('grasas')
        cantidad = request.POST.get('cantidad')
        cantidad_qty = request.POST.get('cantidadQty')
        cantidad_unit = request.POST.get('cantidadUnit')
        imagen = request.FILES.get('imagen')
        
        # Obtener los nutrientes en formato JSON del request
        nutrientes_str = request.POST.get('nutrientes')  # Suponemos que esto es un string JSON
        if nutrientes_str:
            try:
                # Convertir el string JSON en una lista de diccionarios
                nutrientes = json.loads(nutrientes_str)
            except json.JSONDecodeError:
                nutrientes = []
        else:
            nutrientes = []

        # Procesar los nutrientes si es necesario
        # Por ejemplo, puedes transformar la lista en un formato específico
        nutrientes_dict = {}
        for nutriente in nutrientes:
            # Asegúrate de que 'attr_id' y 'value' sean claves válidas en tu JSON
            attr_id = nutriente.get('attr_id')
            value = nutriente.get('value')
            if attr_id and value:
                nutrientes_dict[attr_id] = value

        # Crear o actualizar el alimento
        alimento, created = Alimento.objects.update_or_create(
            nombre=nombre,
            defaults={
                'calorias': calorias,
                'proteinas': proteinas,
                'carbohidratos': carbohidratos,
                'grasas': grasas,
                'cantidad_gramos': cantidad,
                'cantidad_unidades': cantidad_qty,
                'unidad': cantidad_unit,
                'nutrientes': nutrientes,
            }
        )
        
        return redirect('agregar_alimento_en_opcion', opcion_id=opcion.id, usuario_id=opcion.usuario.id)  # Redirige a la vista de nutrición o a donde prefieras

    return render(request, 'gestor/agregar_alimento.html', {'opcion_id': opcion_id, 'usuario_id': opcion.usuario.id})

#Agregar nuevo alimento en base de datos en vista de detalle de comida
def agregar_alimento_detalle(request, opcion_id):
    opcion = get_object_or_404(OpcionMenu, pk=opcion_id)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        calorias = request.POST.get('calorias')
        proteinas = request.POST.get('proteinas')
        carbohidratos = request.POST.get('carbohidratos')
        grasas = request.POST.get('grasas')
        cantidad = request.POST.get('cantidad')
        cantidad_qty = request.POST.get('cantidadQty')
        cantidad_unit = request.POST.get('cantidadUnit')
        
        # Obtener los nutrientes en formato JSON del request
        nutrientes_str = request.POST.get('nutrientes')  # Suponemos que esto es un string JSON
        if nutrientes_str:
            try:
                # Convertir el string JSON en una lista de diccionarios
                nutrientes = json.loads(nutrientes_str)
            except json.JSONDecodeError:
                nutrientes = []
        else:
            nutrientes = []

        # Procesar los nutrientes si es necesario
        # Por ejemplo, puedes transformar la lista en un formato específico
        nutrientes_dict = {}
        for nutriente in nutrientes:
            # Asegúrate de que 'attr_id' y 'value' sean claves válidas en tu JSON
            attr_id = nutriente.get('attr_id')
            value = nutriente.get('value')
            if attr_id and value:
                nutrientes_dict[attr_id] = value

        # Crear o actualizar el alimento
        alimento, created = Alimento.objects.update_or_create(
            nombre=nombre,
            defaults={
                'calorias': calorias,
                'proteinas': proteinas,
                'carbohidratos': carbohidratos,
                'grasas': grasas,
                'cantidad_gramos': cantidad,
                'cantidad_unidades': cantidad_qty,
                'unidad': cantidad_unit,
                'nutrientes': nutrientes,
            }
        )
        
        return redirect('agregar_alimento_en_opcion_detalle', usuario_id=opcion.usuario.id, opcion_id=opcion.id)  # Redirige a la vista de nutrición o a donde prefieras

    return render(request, 'gestor/agregar_alimento_detalle.html', {'opcion_id': opcion_id, 'usuario_id': opcion.usuario.id})

#Agregar alimento en base de datos desde la vista de detalle de opcion de comida
def agregar_alimento_detalle_opcion(request, opcion_id):
    opcion = get_object_or_404(OpcionMenu, pk=opcion_id)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        calorias = request.POST.get('calorias')
        proteinas = request.POST.get('proteinas')
        carbohidratos = request.POST.get('carbohidratos')
        grasas = request.POST.get('grasas')
        cantidad = request.POST.get('cantidad')
        cantidad_qty = request.POST.get('cantidadQty')
        cantidad_unit = request.POST.get('cantidadUnit')
        
        # Obtener los nutrientes en formato JSON del request
        nutrientes_str = request.POST.get('nutrientes')  # Suponemos que esto es un string JSON
        if nutrientes_str:
            try:
                # Convertir el string JSON en una lista de diccionarios
                nutrientes = json.loads(nutrientes_str)
            except json.JSONDecodeError:
                nutrientes = []
        else:
            nutrientes = []

        # Procesar los nutrientes si es necesario
        # Por ejemplo, puedes transformar la lista en un formato específico
        nutrientes_dict = {}
        for nutriente in nutrientes:
            # Asegúrate de que 'attr_id' y 'value' sean claves válidas en tu JSON
            attr_id = nutriente.get('attr_id')
            value = nutriente.get('value')
            if attr_id and value:
                nutrientes_dict[attr_id] = value

        # Crear o actualizar el alimento
        alimento, created = Alimento.objects.update_or_create(
            nombre=nombre,
            defaults={
                'calorias': calorias,
                'proteinas': proteinas,
                'carbohidratos': carbohidratos,
                'grasas': grasas,
                'cantidad_gramos': cantidad,
                'cantidad_unidades': cantidad_qty,
                'unidad': cantidad_unit,
                'nutrientes': nutrientes,
            }
        )
        
        return redirect('agregar_alimento_en_opcion_detalle_opcion', usuario_id=opcion.usuario.id, opcion_id=opcion.id)  # Redirige a la vista agregar alimento en detalle de opcion

    return render(request, 'gestor/agregar_alimento_detalle_opcion.html', {'opcion_id': opcion_id, 'usuario_id': opcion.usuario.id})

#Editar existente
def editar_alimento(request, pk):
    alimento = get_object_or_404(Alimento, pk=pk)
    if request.method == 'POST':
        form = AlimentoForm(request.POST, instance=alimento)
        if form.is_valid():
            form.save()
            return redirect('lista_alimentos')
    else:
        form = AlimentoForm(instance=alimento)
    return render(request, 'gestor/editar_alimento.html', {'form': form})

#Eliminar existente
def eliminar_alimento(request, pk):
    alimento = get_object_or_404(Alimento, pk=pk)
    if request.method == 'POST':
        alimento.delete()
        return redirect('lista_alimentos')
    return render(request, 'gestor/eliminar_alimento.html', {'alimento': alimento})

def buscar_alimentos_base_datos(request):
    if request.method == 'GET':
        query = request.GET.get('query', '')
        if query:
            alimentos = Alimento.objects.filter(nombre__icontains=query)
        else:
            alimentos = Alimento.objects.all()
        
        alimentos_data = []
        for alimento in alimentos:
            alimentos_data.append({
                'id': alimento.id,
                'nombre': alimento.nombre,
                'calorias': alimento.calorias,
                'proteinas': alimento.proteinas,
                'carbohidratos': alimento.carbohidratos,
                'grasas': alimento.grasas,
                'cantidad_gramos': alimento.cantidad_gramos,
                'cantidad_unidades': alimento.cantidad_unidades,
                'unidad': alimento.unidad,
                'imagen_url': alimento.imagen.url if alimento.imagen else '',
                'nutrientes': alimento.nutrientes,
            })
        
        return JsonResponse({'alimentos': alimentos_data})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


def buscar_alimento_nutritionix(request):
    query = request.GET.get('query', '')
    if not query:
        return JsonResponse({'error': 'No query provided'}, status=400)

    url = "https://trackapi.nutritionix.com/v2/search/instant"
    headers = {
        "x-app-id": settings.NUTRITIONIX_APP_ID,
        "x-app-key": settings.NUTRITIONIX_API_KEY,
    }
    params = {
        "query": query,
        "branded": True,
        "common": True,
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return JsonResponse({'error': 'API request failed'}, status=response.status_code)

    data = response.json()
        
    
    results = {
        'common': [],
        'branded': []
    }
    
    # Procesar alimentos genéricos
    for item in data.get('common', []):
        alimento = {
            'nombre': item['food_name'],
            'foto': item['photo']['thumb'],
            'nix_item_id': item.get('nix_item_id'),
            'tag_id': item.get('tag_id'),
            'porcion': item.get('serving_qty', 'N/A'),
            'gramos_porsion': item.get('serving_weight_grams', 'N/A'),
            'nutrientes': item.get('food_nutrients', [])
        }
        results['common'].append(alimento)

    # Procesar alimentos de marca
    for item in data.get('branded', []):
        alimento = {
            'nombre': item['food_name'],
            'foto': item['photo']['thumb'],
            'nix_item_id': item.get('nix_item_id'),
            'tag_id': item.get('tag_id'),
            'porcion': item.get('serving_qty', 'N/A'),
            'gramos_porsion': item.get('serving_weight_grams', 'N/A'),
            'nutrientes': item.get('food_nutrients', [])
        }
        results['branded'].append(alimento)

    return JsonResponse({'alimentos': results})


from django.core.files.base import ContentFile


def guardar_alimento_base_datos(response):
    if response.status_code != 200:
        return {'status': 'error', 'message': 'API request failed', 'status_code': response.status_code}

    data = response.json()
    if not data['foods']:
        return {'status': 'error', 'message': 'No food data found', 'status_code': 404}
    
    alimento_data = data['foods'][0]
    nombre_alimento = alimento_data['food_name']
    calorias = alimento_data.get('nf_calories', 0)
    proteinas = alimento_data.get('nf_protein', 0)
    carbohidratos = alimento_data.get('nf_total_carbohydrate', 0)
    grasas = alimento_data.get('nf_total_fat', 0)
    cantidad_gramos = alimento_data.get('serving_weight_grams', 0)
    cantidad_unidades = alimento_data.get('serving_qty', 0)
    unidad = alimento_data.get('serving_unit', 'N/A')
    foto_url = alimento_data['photo']['thumb']
    nutrientes = alimento_data.get('full_nutrients', [])

    # Descargar la imagen
    response = requests.get(foto_url)
    if response.status_code == 200:
        # Guardar la imagen en un archivo temporal
        image_file = ContentFile(response.content, name=f'{nombre_alimento}.jpg')

        # Crear y guardar el alimento
        alimento, created = Alimento.objects.update_or_create(
            nombre=nombre_alimento,
            defaults={
                'calorias': calorias,
                'proteinas': proteinas,
                'carbohidratos': carbohidratos,
                'grasas': grasas,
                'cantidad_gramos': cantidad_gramos,
                'cantidad_unidades': cantidad_unidades,
                'unidad': unidad,
                'imagen': image_file,
                'nutrientes': nutrientes,
            }
        )
        if created:
            return {'status': 'success', 'message': 'Alimento created successfully', 'alimento': alimento.nombre}
        else:
            return {'status': 'success', 'message': 'Alimento updated successfully', 'alimento': alimento.nombre}

    return {'status': 'error', 'message': 'Failed to download image', 'status_code': 500}

def obtener_detalle_alimento(request):
    nombre = request.GET.get('nombre')
    if not nombre:
        return JsonResponse({'error': 'No food name provided'}, status=400)

    url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        "x-app-id": settings.NUTRITIONIX_APP_ID,
        "x-app-key": settings.NUTRITIONIX_API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "query": nombre,
    }

    response = requests.post(url, headers=headers, json=body)
    if response.status_code != 200:
        return JsonResponse({'error': 'API request failed'}, status=response.status_code)

    data = response.json()
    if not data['foods']:
        return JsonResponse({'error': 'No food data found'}, status=404)

    # Guardado temporal del alimento
    guardado = guardar_alimento_base_datos(response)
    
    if guardado['status'] == 'error':
        return JsonResponse({'error': guardado['message']}, status=guardado.get('status_code', 500))
    
    
    alimento = {
        'nombre': data['foods'][0]['food_name'],
        'calorias': data['foods'][0].get('nf_calories'),
        'proteinas': data['foods'][0].get('nf_protein'),
        'carbohidratos': data['foods'][0].get('nf_total_carbohydrate'),
        'grasas': data['foods'][0].get('nf_total_fat'),
        'foto': data['foods'][0]['photo']['thumb'],
        'serving_weight_grams': data['foods'][0].get('serving_weight_grams'),
        'serving_qty': data['foods'][0].get('serving_qty'),
        'serving_unit': data['foods'][0].get('serving_unit'),
        'nutrientes': data['foods'][0].get('full_nutrients'),
        'guardado': guardado,
    }

    return JsonResponse({'alimento': alimento})


#Vista para imprimir plan de alimentacion
def generar_pdf(request, usuario_id):
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    comidas = Comida.objects.filter(usuario=usuario).order_by('orden')
    
    # Calcular totales y porcentajes
    calorias_objetivo = usuario.objetivo_calorias()
    proteinas, proteinasxkg, carbohidratos, carbohidratosxkg, grasas, grasasxkgs = usuario.porcentaje_macros()
    
    # Preparar los datos de cada comida para la plantilla
    comidas_macronutrientes = [
        {
            'id': comida.id,
            'nombre': comida.nombre,
            'calorias_por_comida': comida.calcular_macronutrientes()['calorias_por_comida'],
            'proteinas_por_comida': comida.calcular_macronutrientes()['proteinas_por_comida'],
            'carbohidratos_por_comida': comida.calcular_macronutrientes()['carbohidratos_por_comida'],
            'grasas_por_comida': comida.calcular_macronutrientes()['grasas_por_comida'],
            'porcentaje_calorias': comida.porcentaje_calorias,
            'opciones_menu': comida.opciones_menu.all(),
        } 
        for comida in comidas
    ]

    
    # Obtener datos adicionales
    calorias_objetivo = usuario.objetivo_calorias()
    proteinas, proteinasxkg, carbohidratos, carbohidratosxkg, grasas, grasasxkgs = usuario.porcentaje_macros()
    
    # Renderizar plantilla HTML
    html_string = render_to_string('gestor/plan_alimentacion.html', {
        'usuario': usuario,
        'comidas': comidas_macronutrientes,
        'calorias_objetivo': calorias_objetivo,
        'proteinas': proteinas,
        'proteinasxkg': proteinasxkg,
        'carbohidratos': carbohidratos,
        'carbohidratosxkg': carbohidratosxkg,
        'grasas': grasas,
        'grasasxkgs': grasasxkgs
    })
    
    # Crear PDF a partir de la plantilla HTML
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Plan_Alimentacion_{usuario.nombre}.pdf"'
    
    pisa_status = pisa.CreatePDF(html_string, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF: %s' % pisa_status.err)
    
    return response





#vistas anteriores


#guardar en base de datos
# def actualizar_base_datos(request):
#     if request.method == 'POST':
#         query = request.POST.get('query')
#         api_key = settings.USDA_API_KEY
#         obtener_datos_alimentos(api_key, query)
#         return redirect('lista_alimentos')
#     return render(request, 'gestor/actualizar_base_datos_alimentos.html')

# def buscar_alimento_usda(request):
#     query = request.GET.get('query', '')
#     if query:
#         url = f'https://api.nal.usda.gov/fdc/v1/foods/search?api_key={settings.USDA_API_KEY}&query={query}'
#         response = requests.get(url)
#         if response.status_code == 200:
#             data = response.json()
#             alimentos = []
#             for item in data.get('foods', []):
#                 alimento = {
#                     'nombre': item.get('description'),
#                     'calorias': next((nutrient['value'] for nutrient in item['foodNutrients'] if nutrient['nutrientName'] == 'Energy'), 0),
#                     'proteinas': next((nutrient['value'] for nutrient in item['foodNutrients'] if nutrient['nutrientName'] == 'Protein'), 0),
#                     'carbohidratos': next((nutrient['value'] for nutrient in item['foodNutrients'] if nutrient['nutrientName'] == 'Carbohydrate, by difference'), 0),
#                     'grasas': next((nutrient['value'] for nutrient in item['foodNutrients'] if nutrient['nutrientName'] == 'Total lipid (fat)'), 0),
#                 }
#                 alimentos.append(alimento)
#             return JsonResponse({'alimentos': alimentos})
#     return JsonResponse({'alimentos': []})

# def agregar_alimento_en_opcion(request, opcion_id):
#     opcion = OpcionMenu.objects.get(pk=opcion_id)
#     if request.method == 'POST':
#         form = AlimentoEnOpcionForm(request.POST)
#         if form.is_valid():
#             alimento_en_opcion = form.save(commit=False)
#             alimento_en_opcion.opcion_menu = opcion
#             alimento_en_opcion.save()
#             return redirect('vista_nutricion', pk=opcion.comida.pk)
#     else:
#         form = AlimentoEnOpcionForm()
    
#     return render(request, 'gestor/agregar_alimento_en_opcion.html', {
#         'form': form,
#         'opcion': opcion,
#     })

#Buscar usando API
# def buscar_alimento(request):
#     query = request.GET.get('query', '')
#     api_key = settings.USDA_API_KEY
#     url = f'https://api.nal.usda.gov/fdc/v1/foods/search?query={query}&api_key={api_key}'
#     response = requests.get(url)
#     data = response.json()
    
#     alimentos = []
#     for item in data['foods']:
#         nombre = item['description']
#         calorias = next((nutrient['value'] for nutrient in item['foodNutrients'] if nutrient['nutrientName'] == 'Energy'), 0)
#         proteinas = next((nutrient['value'] for nutrient in item['foodNutrients'] if nutrient['nutrientName'] == 'Protein'), 0)
#         carbohidratos = next((nutrient['value'] for nutrient in item['foodNutrients'] if nutrient['nutrientName'] == 'Carbohydrate, by difference'), 0)
#         grasas = next((nutrient['value'] for nutrient in item['foodNutrients'] if nutrient['nutrientName'] == 'Total lipid (fat)'), 0)
        
#         alimentos.append({
#             'nombre': nombre,
#             'calorias': calorias,
#             'proteinas': proteinas,
#             'carbohidratos': carbohidratos,
#             'grasas': grasas,
#         })
    
#     return JsonResponse({'alimentos': alimentos})

# def buscar_alimento_nutritionix(request):
#     query = request.GET.get('query', '')
#     if not query:
#         return JsonResponse({'error': 'No query provided'}, status=400)

#     url = "https://trackapi.nutritionix.com/v2/search/instant"
#     headers = {
#         "x-app-id": settings.NUTRITIONIX_APP_ID,
#         "x-app-key": settings.NUTRITIONIX_API_KEY,
#     }
#     params = {
#         "query": query,
#         "branded": True,
#         "common": True,
#     }

#     response = requests.get(url, headers=headers, params=params)
#     if response.status_code != 200:
#         return JsonResponse({'error': 'API request failed'}, status=response.status_code)

#     data = response.json()
    
#     results = []
#     for item in data.get('common', []):
#         alimento = {
#             'nombre': item['food_name'],
#             'foto': item['photo']['thumb'],
#             'nix_item_id': item.get('nix_item_id'),
#             'tag_id': item.get('tag_id')
#         }
#         results.append(alimento)

#     for item in data.get('branded', []):
#         alimento = {
#             'nombre': item['food_name'],
#             'foto': item['photo']['thumb'],
#             'nix_item_id': item.get('nix_item_id'),
#             'tag_id': item.get('tag_id')
#         }
#         results.append(alimento)

#     return JsonResponse({'alimentos': results})





# def vista_nutricion(request, pk):
#     usuario = get_object_or_404(Usuario, pk=pk)
#     comidas = Comida.objects.filter(usuario=usuario).order_by('orden')
#     alimentos = Alimento.objects.filter(pk=pk)
#     objetivo_entrenamiento = usuario.objetivo_entrenamiento
#     calorias = usuario.objetivo_calorias()
#     proteinas, proteinasxkg, carbohidratos, carbohidratosxkg, grasas, grasasxkgs = usuario.porcentaje_macros()
    
#     if request.method == 'POST':
#         usuario.macros_proteina = float(request.POST.get('macros_proteina'))
#         usuario.macros_carbohidratos = float(request.POST.get('macros_carbohidratos'))
#         usuario.macros_grasas = float(request.POST.get('macros_grasas'))
#         usuario.save()
        
#         for comida in comidas:
#             porcentaje = request.POST.get(f'porcentaje_{comida.id}')
#             if porcentaje is not None:
#                 comida.porcentaje_calorias = float(porcentaje)
#                 comida.save()
                
#         proteinas, proteinasxkg, carbohidratos, carbohidratosxkg, grasas, grasasxkgs = usuario.porcentaje_macros()
    
#     porcentajes_calorias = usuario.obtener_porcentajes_calorias()
    
#     comidas_macronutrientes = [
#         {
#             'nombre': comida.nombre,
#             'calorias_por_comida': comida.calcular_macronutrientes()['calorias_por_comida'],
#             'proteinas_por_comida': comida.calcular_macronutrientes()['proteinas_por_comida'],
#             'carbohidratos_por_comida': comida.calcular_macronutrientes()['carbohidratos_por_comida'],
#             'grasas_por_comida': comida.calcular_macronutrientes()['grasas_por_comida'],
#             'porcentaje': comida.porcentaje_calorias,
#             'id': comida.id
#         }
#         for comida in comidas
#     ]
    
#     context = {
#         'usuario': usuario,
#         'comidas' : comidas,
#         'alimentos' : alimentos,
#         'calorias_objetivo': calorias,
#         'objetivo_entrenamiento': objetivo_entrenamiento, 
#         'proteinas': proteinas,
#         'protxkg' : proteinasxkg,
#         'carbxkg' : carbohidratosxkg,
#         'grasxkg' : grasasxkgs,
#         'carbohidratos': carbohidratos,
#         'grasas': grasas,
#         'macros_proteina': usuario.macros_proteina,
#         'macros_carbohidratos': usuario.macros_carbohidratos,
#         'macros_grasas': usuario.macros_grasas,
#         'porcentajes_calorias': porcentajes_calorias,
#         'comidas_macronutrientes': comidas_macronutrientes,
#     }

#     return render(request, 'gestor/vista_nutricion.html', context)



# def editar_alimento_en_opcion(request, pk):
#     alimento_en_opcion = get_object_or_404(AlimentoEnOpcion, pk=pk)
#     if request.method == 'POST':
#         form = AlimentoEnOpcionForm(request.POST, instance=alimento_en_opcion)
#         if form.is_valid():
#             form.save()
#             return redirect('vista_nutricion', pk=alimento_en_opcion.opcion_menu.comida.usuario.pk)
#     else:
#         form = AlimentoEnOpcionForm(instance=alimento_en_opcion)
#     return render(request, 'gestor/editar_alimento_en_opcion.html', {'form': form, 'alimento_en_opcion': alimento_en_opcion})