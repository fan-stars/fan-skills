<?php
use App\Http\Controllers\ProductController;
Route::post('/api/products', [ProductController::class, 'store']);
