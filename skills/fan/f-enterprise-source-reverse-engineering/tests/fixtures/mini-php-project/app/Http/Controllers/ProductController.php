<?php
namespace App\Http\Controllers;
use App\Http\Requests\ProductRequest;
use App\Services\ProductService;
class ProductController {
    public function __construct(private ProductService $service) {}
    public function store(ProductRequest $request) {
        return $this->service->create($request->validated());
    }
}
