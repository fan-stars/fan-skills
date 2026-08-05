<?php
namespace App\Http\Requests;
class ProductRequest {
    public function rules(): array { return ['name' => 'required', 'sku' => 'required']; }
    public function validated(): array { return ['name' => 'Demo', 'sku' => 'SKU-1']; }
}
