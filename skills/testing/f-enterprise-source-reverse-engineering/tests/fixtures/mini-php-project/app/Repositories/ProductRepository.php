<?php
namespace App\Repositories;
class ProductRepository {
    public function create(array $input): array {
        return Product::query()->insertGetId(['name' => $input['name'], 'sku' => $input['sku'], 'status' => 'DRAFT']);
    }
}
