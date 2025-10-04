from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .models import Category, Product, Cart, Order, OrderItem, UserProfile
from django.db.models import Sum
from decimal import Decimal
from django.contrib.auth.models import User

def home(request):
    categories = Category.objects.all()
    featured_products = Product.objects.all()[:8]
    return render(request, 'myapp/home.html', {
        'categories': categories,
        'featured_products': featured_products
    })

def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    return render(request, 'myapp/category_products.html', {
        'category': category,
        'products': products
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Get related products from the same category, excluding the current product
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    return render(request, 'myapp/product_detail.html', {
        'product': product,
        'related_products': related_products
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': 1}
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f"{product.name} added to cart!")
    return redirect('cart')

@login_required
def cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'myapp/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def update_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')

@login_required
def remove_from_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    cart_item.delete()
    messages.success(request, "Item removed from cart!")
    return redirect('cart')

@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty!")
        return redirect('cart')
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'myapp/checkout.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def place_order(request):
    if request.method == 'POST':
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return redirect('cart')

        # Calculate total amount
        total_amount = sum(item.product.price * item.quantity for item in cart_items)

        # Create order with new fields
        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            full_name=request.POST.get('full_name'),
            phone_number=request.POST.get('phone_number'),
            city=request.POST.get('city'),
            address=request.POST.get('address'),
            payment_method=request.POST.get('payment_method')
        )

        # Handle JazzCash payment details
        if request.POST.get('payment_method') == 'jazzcash':
            order.jazzcash_number = request.POST.get('jazzcash_number')
            if 'payment_screenshot' in request.FILES:
                order.payment_screenshot = request.FILES['payment_screenshot']
            order.save()

        # Create order items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )

        # Clear the cart
        cart_items.delete()

        return redirect('order_confirmation', order_id=order.id)

    return redirect('cart')

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'myapp/order_confirmation.html', {
        'order': order
    })

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'myapp/order_history.html', {
        'orders': orders
    })

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect('register')
        
        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(user=user)
        
        login(request, user)
        messages.success(request, "Registration successful!")
        return redirect('home')
    
    return render(request, 'myapp/register.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password!")
    
    return render(request, 'myapp/login.html')

@login_required
def profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()

        profile = user.userprofile
        profile.phone_number = request.POST.get('phone_number', '')
        profile.address = request.POST.get('address', '')
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('profile')

    return render(request, 'myapp/profile.html')

def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully!")
    return redirect('home')

def products(request):
    # Get all products
    products = Product.objects.all()
    categories = Category.objects.all()

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(name__icontains=search_query) | products.filter(description__icontains=search_query)

    # Category filter
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    # Price range filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Stock status filter
    in_stock = request.GET.get('in_stock')
    low_stock = request.GET.get('low_stock')
    if in_stock:
        products = products.filter(stock__gt=10)
    if low_stock:
        products = products.filter(stock__gt=0, stock__lte=10)

    # Sorting
    sort = request.GET.get('sort')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')
    elif sort == 'newest':
        products = products.order_by('-created_at')

    return render(request, 'myapp/products.html', {
        'products': products,
        'categories': categories
    })

def about(request):
    return render(request, 'myapp/about.html')
