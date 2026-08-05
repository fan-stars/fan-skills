<?php
namespace App\Services;
use App\Repositories\ProductRepository;
use App\Services\InventoryService;
use App\Jobs\SyncProductJob;
class ProductService {
    public function __construct(private ProductRepository $repository, private InventoryService $inventory) {}
    public function create(array $input): array {
        return DB::transaction(function () use ($input) {
            $product = $this->repository->create($input);
            $this->inventory->reserve($product['sku']);
            SyncProductJob::dispatch($product['id']);
            return $product;
        });
    }
}
