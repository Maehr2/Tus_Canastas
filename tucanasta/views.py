from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST
from .models import Producto, Supermercado
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth import update_session_auth_hash
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from .forms import CustomUserCreationForm
from django.utils import timezone
from django.core.mail import send_mail
from .forms import UserUpdateForm, SimplePasswordChangeForm
# importa modelos (incluye Cotizacion y CotizacionItem)
from .models import Producto, Supermercado, Cotizacion, CotizacionItem
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import PymeProductForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import PymeRegistrationForm, PymeProductForm
from .models import Pyme, Supermercado, Producto
from django.shortcuts import redirect
from django.conf import settings

# --- agregar_cotizacion ---

def get_or_create_open_cotizacion(user):
    cot, created = Cotizacion.objects.get_or_create(usuario=user, status='open')
    return cot

@login_required
@require_POST
def agregar_cotizacion(request, producto_id=None):
    """
    Agregar producto a la cotización abierta del usuario.
    Expects POST param 'product_id' and optional 'cantidad'.
    Returns JSON (AJAX).
    """
    product_id = producto_id or request.POST.get('product_id') or request.POST.get('pk')
    try:
        cantidad = int(request.POST.get('cantidad', 1))
    except (TypeError, ValueError):
        cantidad = 1

    if not product_id:
        return JsonResponse({'ok': False, 'error': 'product_id faltante'}, status=400)

    producto = get_object_or_404(Producto, pk=product_id)

    cot = get_or_create_open_cotizacion(request.user)

    item, created = CotizacionItem.objects.get_or_create(
        cotizacion=cot,
        producto=producto,
        defaults={'cantidad': cantidad, 'precio_unidad': producto.precio}
    )

    if not created:
        item.cantidad = item.cantidad + cantidad
        item.precio_unidad = producto.precio
        item.save()

    return JsonResponse({
        'ok': True,
        'item_id': item.pk,
        'producto': producto.nombre,
        'cantidad': item.cantidad,
        'subtotal': item.subtotal,
        'total': cot.total
    })


# 2) Ver cotización (pantalla)
@login_required
def ver_cotizacion(request):
    cot = get_or_create_open_cotizacion(request.user)
    items = cot.items.select_related('producto', 'producto__supermercado').all()

    # pasar también el total
    total = cot.total

    return render(request, 'cotizacion.html', {
        'cotizacion': cot,
        'items': items,
        'total': total,
    })


# 3) Actualizar cantidad (AJAX POST)
@login_required
@require_POST
def actualizar_item(request):
    item_id = request.POST.get('item_id')
    cantidad = int(request.POST.get('cantidad', 1))
    item = get_object_or_404(CotizacionItem, pk=item_id, cotizacion__usuario=request.user)
    if cantidad <= 0:
        item.delete()
        msg = 'deleted'
    else:
        item.cantidad = cantidad
        item.save()
        msg = 'updated'
    # recompute total
    total = item.cotizacion.total if hasattr(item, 'cotizacion') else 0
    return JsonResponse({'ok': True, 'msg': msg, 'total': total})


# 4) Eliminar item (AJAX POST)
@login_required
@require_POST
def eliminar_item(request):
    item_id = request.POST.get('item_id')
    item = get_object_or_404(CotizacionItem, pk=item_id, cotizacion__usuario=request.user)
    cot = item.cotizacion
    item.delete()
    return JsonResponse({'ok': True, 'total': cot.total})


# 5) Guardar cotización (cambiar status a 'saved')
@login_required
@require_POST
def guardar_cotizacion(request):
    """
    Marca la cotización abierta del usuario como 'saved' y devuelve JSON con id.
    Opcional: recibe 'nombre' en POST para nombrar la cotización.
    """
    cot = Cotizacion.objects.filter(usuario=request.user, status='open').first()
    if not cot:
        return JsonResponse({'ok': False, 'error': 'No hay cotización abierta'}, status=404)

    nombre = request.POST.get('nombre') or f'Cotización {timezone.localtime().strftime("%Y-%m-%d %H:%M")}'
    cot.nombre = nombre
    cot.status = 'saved'
    cot.save()

    return JsonResponse({'ok': True, 'cotizacion_id': cot.pk})


# Lista de cotizaciones del usuario (guardadas / abiertas / enviadas)
@login_required
def mis_cotizaciones(request):
    cotizaciones = (
        Cotizacion.objects
        .filter(usuario=request.user)
        .prefetch_related('items__producto', 'items__producto__supermercado')
        .order_by('-fecha_creacion')
    )
    return render(request, 'mis_cotizaciones.html', {'cotizaciones': cotizaciones})


# Reabrir una cotización (ponerla como 'open')
@login_required
@require_POST
def reabrir_cotizacion(request):
    cot_id = request.POST.get('cot_id')
    cot = get_object_or_404(Cotizacion, pk=cot_id, usuario=request.user)

    # Si quieres permitir solo una abierta, cerramos las otras abiertas
    Cotizacion.objects.filter(usuario=request.user, status='open').exclude(pk=cot.pk).update(status='saved')

    cot.status = 'open'
    cot.save()
    return JsonResponse({'ok': True, 'cotizacion_id': cot.pk})


# Eliminar cotización completa
@login_required
@require_POST
def eliminar_cotizacion(request):
    cot_id = request.POST.get('cot_id')
    cot = get_object_or_404(Cotizacion, pk=cot_id, usuario=request.user)
    cot.delete()
    return JsonResponse({'ok': True})


# --- ajustes (placeholder) ---
@login_required
def ajustes(request):
    """
    Página de ajustes:
    - maneja update de perfil y cambio de contraseña
    - prepara cotizacion y cot_items para el mini-cart (igual que en comparador_view)
    """
    user = request.user

    # Manejo de POSTs
    if request.method == 'POST':
        if 'profile_submit' in request.POST:
            profile_form = UserUpdateForm(request.POST, instance=user)
            password_form = SimplePasswordChangeForm(user=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Datos actualizados correctamente.")
                return redirect('ajustes')
            else:
                messages.error(request, "Corrige los errores en el formulario de datos.")
        elif 'password_submit' in request.POST:
            profile_form = UserUpdateForm(instance=user)
            password_form = SimplePasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Contraseña actualizada correctamente.")
                return redirect('ajustes')
            else:
                messages.error(request, "Corrige los errores en el formulario de contraseña.")
        else:
            profile_form = UserUpdateForm(instance=user)
            password_form = SimplePasswordChangeForm(user=user)
    else:
        profile_form = UserUpdateForm(instance=user)
        password_form = SimplePasswordChangeForm(user=user)

    # --- preparar mini-cart: cotizacion abierta y items (igual que en comparador_view) ---
    cot = None
    cot_items = []
    if request.user.is_authenticated:
        cot = Cotizacion.objects.filter(usuario=request.user, status='open').prefetch_related('items__producto', 'items__producto__supermercado').first()
        if cot:
            cot_items = list(cot.items.select_related('producto', 'producto__supermercado').all())

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
        'cotizacion': cot,
        'cot_items': cot_items,
    }
    return render(request, 'ajustes.html', context)


def logout_view(request):
    """
    Cierra la sesión y redirige al index.
    Uso: path('logout/', views.logout_view, name='logout')
    """
    logout(request)
    return redirect('index')




# en tucanasta/views.py (al principio de archivo ya tienes imports; añade:)


@login_required
def pyme_ingresar(request):
    """
    Página para que PYMES ingresen productos.
    - Permite seleccionar supermercado existente o crear uno nuevo (new_supermercado_name).
    - Requiere login.
    """
    # preparar mini-cart (igual que en otras vistas para mantener consistencia UI)
    cot = None
    cot_items = []
    if request.user.is_authenticated:
        cot = Cotizacion.objects.filter(usuario=request.user, status='open').prefetch_related('items__producto').first()
        if cot:
            cot_items = list(cot.items.select_related('producto', 'producto__supermercado').all())

    if request.method == "POST":
        form = PymeProductForm(request.POST)
        new_super_name = request.POST.get('new_supermercado_name', '').strip()
        new_super_url = request.POST.get('new_supermercado_url', '').strip()

        # Validamos que haya supermercado seleccionado o uno nuevo
        if not form.cleaned_data if not form.is_bound else False:
            # just continue -- form.is_valid will check fields
            pass

        if form.is_valid():
            # Si el usuario quiere crear supermercado nuevo:
            if new_super_name:
                supermercado, created = Supermercado.objects.get_or_create(
                    nombre=new_super_name,
                    defaults={'url_principal': new_super_url or None}
                )
            else:
                supermercado = form.cleaned_data.get('supermercado')

            if not supermercado:
                messages.error(request, "Debes seleccionar un supermercado o crear uno nuevo.")
            else:
                producto = form.save(commit=False)
                producto.supermercado = supermercado
                producto.save()
                messages.success(request, "Producto agregado correctamente. Será visible después de revisión.")
                return redirect('producto_detalle', producto_id=producto.pk)
        else:
            messages.error(request, "Corrige los errores del formulario.")
    else:
        form = PymeProductForm()

    context = {
        'form': form,
        'cotizacion': cot,
        'cot_items': cot_items,
    }
    return render(request, 'pyme_ingresar.html', context)




@login_required
def pyme_registro(request):
    # si ya tiene pyme, redirige al dashboard
    if hasattr(request.user, 'pyme'):
        messages.info(request, "Ya tienes una cuenta Pyme. Accediendo al panel.")
        return redirect('pyme_dashboard')

    if request.method == 'POST':
        form = PymeRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            pyme = form.save(commit=False)
            pyme.user = request.user
            # crear Supermercado con el nombre de la pyme (si no existe)
            supermercado, created = Supermercado.objects.get_or_create(
                nombre=pyme.nombre,
                defaults={'url_principal': pyme.web or None}
            )
            pyme.supermercado = supermercado
            pyme.approved = False
            # guardar documento si subido (form ya lo maneja)
            pyme.save()
            messages.success(request, "Registro Pyme creado. Tu tienda quedó pendiente de revisión.")
            return redirect('pyme_dashboard')
        else:
            print("DEBUG PymeRegistrationForm errors:", form.errors.as_json())
            messages.error(request, "Corrige los errores del formulario.")
    else:
        form = PymeRegistrationForm()

@login_required
def pyme_dashboard(request):
    # preparar mini-cart (si quieres mantener coherencia con header)
    cot = None
    cot_items = []
    if request.user.is_authenticated:
        cot = Cotizacion.objects.filter(usuario=request.user, status='open').prefetch_related('items__producto').first()
        if cot:
            cot_items = list(cot.items.select_related('producto', 'producto__supermercado').all())

    # asegurar que la cuenta pyme exista
    pyme = getattr(request.user, 'pyme', None)
    if not pyme:
        messages.info(request, "Primero crea tu Pyme.")
        return redirect('pyme_registro')

    productos = Producto.objects.filter(supermercado=pyme.supermercado).order_by('-fecha_actualizacion')

    if request.method == 'POST':
        form = PymeProductForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            # precio viene limpio desde form.cleaned_data['precio'] (float)
            producto.precio = form.cleaned_data['precio']
            producto.moneda = form.cleaned_data['moneda']
            producto.supermercado = pyme.supermercado
            producto.disponible = False  # pendiente revisión
            producto.save()
            messages.success(request, "Producto enviado. Quedará pendiente de revisión.")
            return redirect('pyme_dashboard')
        else:
            # debug server: imprimir errores en consola del runserver
            print("DEBUG PymeProductForm errors:", form.errors.as_json())
            messages.error(request, "Corrige los errores del formulario. Revisa los detalles en cada campo.")
    else:
        form = PymeProductForm(initial={'moneda': 'CLP'})

    context = {
        'pyme': pyme,
        'form': form,
        'productos': productos,
        'cotizacion': cot,
        'cot_items': cot_items,
    }
    return render(request, 'pyme_dashboard.html', context)





# 🏠 Página de inicio
def index(request):
    return render(request, 'index.html')

# 💬 Vista básica de comparador
def comparador(request):
    tipos = Producto.objects.values_list('tipo', flat=True).distinct().order_by('tipo')
    return render(request, 'comparador.html', {'tipos': tipos})

# 🧾 Registro de usuarios
def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("index")
    else:
        form = CustomUserCreationForm()
    return render(request, "signup.html", {"form": form})

# 🔐 Login de usuarios
def login_view(request):
    """
    Login personalizado:
    - muestra mensajes en español con django.contrib.messages
    - preserva el username para rellenar el input después de un intento fallido
    - respeta el parámetro 'next' (redirige allí si existe)
    """
    # prioriza next en POST (form) o GET (por ejemplo redirección desde @login_required)
    next_url = request.POST.get('next') or request.GET.get('next') or None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"¡Bienvenido/a, {user.username}! Sesión iniciada correctamente.")
            # redirige al next si viene, sino al comparador
            return redirect(next_url or "comparador")
        else:
            # Mensaje genérico por seguridad (no revelar existencia de usuario)
            messages.error(request, "Usuario o contraseña incorrectos. Intenta de nuevo.")
            # continúa al render para mostrar el mensaje y mantener el campo username

    # GET o POST fallido — render con prefill opcional del username
    # (tu template ya usa request.POST.username, pero pasamos tambien por contexto por si quieres usarlo)
    context = {
        "username_prefill": request.POST.get("username", "") if request.method == "POST" else "",
    }
    return render(request, "login.html", context)

# 🛒 Vista principal con productos por supermercado
def comparador_view(request):
    supermercados = Supermercado.objects.all().order_by('nombre')

    data_supermercados = []
    for s in supermercados:
        productos = (
            Producto.objects.filter(supermercado=s, disponible=True)
            .order_by('-fecha_actualizacion')[:10]
        )
        for p in productos:
            if not p.imagen_url:
                p.imagen_url = "/static/img/placeholder.png"

        data_supermercados.append({
            "supermercado": s,
            "productos": productos,
        })

    tipos = Producto.objects.values_list('tipo', flat=True).distinct().order_by('tipo')

    # --- NUEVO: obtener cotización abierta si el usuario está autenticado ---
    cot = None
    cot_items = []
    if request.user.is_authenticated:
        cot = Cotizacion.objects.filter(usuario=request.user, status='open').prefetch_related('items__producto').first()
        if cot:
            cot_items = list(cot.items.select_related('producto', 'producto__supermercado').all())

    return render(request, 'comparador.html', {
        "data_supermercados": data_supermercados,
        "tipos": tipos,
        "cotizacion": cot,
        "cot_items": cot_items,
    })
    
    
# 📦 Productos por categoría
def productos_por_categoria(request, tipo):
    productos = Producto.objects.filter(tipo__iexact=tipo).order_by('nombre', 'supermercado__nombre')
    tipos = Producto.objects.values_list('tipo', flat=True).distinct().order_by('tipo')
    return render(request, 'productos_categoria.html', {'tipo': tipo, 'productos': productos, 'tipos': tipos})

# 🔍 Detalle de producto con comparación de precios
def producto_detalle(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    similares = Producto.objects.filter(nombre__icontains=producto.nombre, tipo=producto.tipo).order_by('precio')
    tipos = Producto.objects.values_list('tipo', flat=True).distinct().order_by('tipo')
    return render(request, 'producto_detalle.html', {
        'producto': producto,
        'similares': similares,
        'tipos': tipos
    })
    


# 📦 Productos por categoría con filtros y ordenamiento
def productos_por_categoria(request, tipo):
    # Filtrar productos por categoría
    productos = Producto.objects.filter(tipo__iexact=tipo, disponible=True)
    tipos = Producto.objects.values_list('tipo', flat=True).distinct().order_by('tipo')
    # Filtros GET
    q = request.GET.get('q')
    ordenar = request.GET.get('ordenar')
    marca_filtro = request.GET.getlist('marca')
    tienda_filtro = request.GET.getlist('tienda')

    # Búsqueda
    if q:
        productos = productos.filter(nombre__icontains=q)

    # Filtrar por marca
    if marca_filtro:
        productos = productos.filter(marca__in=marca_filtro)

    # Filtrar por tienda
    if tienda_filtro:
        productos = productos.filter(supermercado__nombre__in=tienda_filtro)

    # Ordenar resultados
    if ordenar == "precio_asc":
        productos = productos.order_by("precio")
    elif ordenar == "precio_desc":
        productos = productos.order_by("-precio")
    elif ordenar == "nombre_asc":
        productos = productos.order_by("nombre")

    # Obtener marcas únicas
    marcas_query = (
        Producto.objects.filter(tipo__iexact=tipo)
        .exclude(marca__isnull=True)
        .exclude(marca__exact="")
        .values_list("marca", flat=True)
    )
    marcas = sorted(set(m.strip().title() for m in marcas_query if m))

    # Obtener tiendas únicas
    tiendas = (
        Supermercado.objects.filter(productos__tipo__iexact=tipo)
        .values_list("nombre", flat=True)
        .distinct()
        .order_by("nombre")
    )

    # Asegurar placeholder en las imágenes (facilita render JS/HTML)
    for p in productos:
        if not p.imagen_url:
            p.imagen_url = "/static/img/placeholder.png"

    # --- Obtener cotización abierta y sus items (igual que en comparador_view) ---
    cot = None
    cot_items = []
    if request.user.is_authenticated:
        cot = (
            Cotizacion.objects
            .filter(usuario=request.user, status='open')
            .prefetch_related('items__producto', 'items__producto__supermercado')
            .first()
        )
        if cot:
            cot_items = list(cot.items.select_related('producto', 'producto__supermercado').all())

    context = {
        "tipo": tipo,
        "tipos": tipos,
        "productos": productos,
        "marcas": marcas,
        "tiendas": tiendas,
        "marca_filtro": marca_filtro,
        "tienda_filtro": tienda_filtro,
        "ordenar": ordenar,
        # mini-cart context:
        "cotizacion": cot,
        "cot_items": cot_items,
    }

    return render(request, "productos_categoria.html", context)

@staff_member_required
@require_POST
def aprobar_pyme(request, pk):
    pyme = get_object_or_404(Pyme, pk=pk)
    pyme.approved = True
    pyme.save()

    # opcional: notificar por mensaje y por email (si configuras email)
    messages.success(request, f'Pyme "{pyme.nombre}" aprobada y activada.')
    # ejemplo email (requiere config email)
    # send_mail('Tu Pyme fue aprobada', 'Tu Pyme ha sido aprobada...', 'from@example.com', [pyme.user.email])

    return redirect('revisar_productos')

@staff_member_required
@require_POST
def rechazar_pyme(request, pk):
    pyme = get_object_or_404(Pyme, pk=pk)
    nombre = pyme.nombre
    # opcional: elimina la pyme y no tocar supermercado
    pyme.delete()
    messages.info(request, f'Pyme "{nombre}" rechazada y eliminada.')
    return redirect('revisar_productos')



def revisar_productos(request):
    pendientes = Producto.objects.filter(disponible=False).select_related('supermercado').order_by('-fecha_actualizacion')
    pymes_pendientes = Pyme.objects.filter(approved=False).select_related('user').order_by('-fecha_creacion')
    return render(request, 'panel-admin/revisar_productos.html', {
        'pendientes': pendientes,
        'pymes_pendientes': pymes_pendientes,
    })

@staff_member_required
@require_POST
def aprobar_producto(request, pk):
    """
    Aprobar (publicar) un producto -> disponible = True
    POST only.
    """
    producto = get_object_or_404(Producto, pk=pk)
    producto.disponible = True
    producto.save()
    messages.success(request, f'Producto "{producto.nombre}" aprobado y publicado.')
    # opcional: mandar notificación/email a la pyme (no implementado aquí)
    return redirect('revisar_productos')


@staff_member_required
@require_POST
def rechazar_producto(request, pk):
    """
    Rechazar producto. Por simplicidad lo borramos.
    Si prefieres mantener un historial, cambia esto para marcar un campo 'rechazado' en el modelo.
    """
    producto = get_object_or_404(Producto, pk=pk)
    nombre = producto.nombre
    producto.delete()
    messages.info(request, f'Producto "{nombre}" rechazado y eliminado.')
    return redirect('revisar_productos')



@staff_member_required
def editar_producto_admin(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == "POST":
        # USAR EL MISMO FORMULARIO DE PYME ✅
        form = PymeProductForm(request.POST, instance=producto)

        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado correctamente.")
            return redirect('revisar_productos')
        else:
            messages.error(request, "Hay errores en el formulario, revisa los campos.")
    else:
        form = PymeProductForm(instance=producto)

    return render(request, "panel-admin/editar_producto.html", {
        "form": form,
        "producto": producto,
    })