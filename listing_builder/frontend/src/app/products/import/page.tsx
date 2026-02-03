// frontend/src/app/products/import/page.tsx
// Purpose: Product import form (single and batch)
// NOT for: Product editing or optimization

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { importSingleProduct, importBatchProducts } from '@/lib/api/import'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useToast } from '@/lib/hooks/useToast'
import { Upload, Plus, Trash2 } from 'lucide-react'

interface ProductForm {
  title: string
  description: string
  bullet_points: string[]
  asin?: string
  brand?: string
  price?: number
  category?: string
}

export default function ImportPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [products, setProducts] = useState<ProductForm[]>([
    {
      title: '',
      description: '',
      bullet_points: [''],
      asin: '',
      brand: '',
      price: undefined,
      category: '',
    },
  ])

  const importMutation = useMutation({
    mutationFn: async () => {
      if (products.length === 1) {
        return await importSingleProduct(products[0])
      } else {
        return await importBatchProducts({ products })
      }
    },
    onSuccess: (data) => {
      toast({
        title: 'Import successful',
        description: products.length === 1
          ? 'Product imported successfully'
          : `Imported ${products.length} products`,
      })
      router.push('/products')
    },
    onError: (error: Error) => {
      toast({
        title: 'Import failed',
        description: error.message,
        variant: 'destructive',
      })
    },
  })

  const addProduct = () => {
    setProducts([
      ...products,
      {
        title: '',
        description: '',
        bullet_points: [''],
        asin: '',
        brand: '',
        price: undefined,
        category: '',
      },
    ])
  }

  const removeProduct = (index: number) => {
    if (products.length > 1) {
      setProducts(products.filter((_, i) => i !== index))
    }
  }

  const updateProduct = (index: number, field: keyof ProductForm, value: unknown) => {
    const updated = [...products]
    updated[index] = { ...updated[index], [field]: value }
    setProducts(updated)
  }

  const addBulletPoint = (productIndex: number) => {
    const updated = [...products]
    updated[productIndex].bullet_points.push('')
    setProducts(updated)
  }

  const updateBulletPoint = (productIndex: number, bulletIndex: number, value: string) => {
    const updated = [...products]
    updated[productIndex].bullet_points[bulletIndex] = value
    setProducts(updated)
  }

  const removeBulletPoint = (productIndex: number, bulletIndex: number) => {
    const updated = [...products]
    if (updated[productIndex].bullet_points.length > 1) {
      updated[productIndex].bullet_points = updated[productIndex].bullet_points.filter(
        (_, i) => i !== bulletIndex
      )
      setProducts(updated)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Validate
    const hasErrors = products.some(
      (p) => !p.title || !p.description || p.bullet_points.some((b) => !b)
    )

    if (hasErrors) {
      toast({
        title: 'Validation error',
        description: 'Please fill in all required fields',
        variant: 'destructive',
      })
      return
    }

    importMutation.mutate()
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold text-white">Import Products</h1>
        <p className="text-gray-400 mt-2">
          Add new products to your listing automation system
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {products.map((product, productIndex) => (
          <Card key={productIndex}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Product {productIndex + 1}</CardTitle>
                  <CardDescription>Fill in product details</CardDescription>
                </div>
                {products.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removeProduct(productIndex)}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Title */}
              <div>
                <label className="text-sm font-medium text-white">
                  Title <span className="text-red-500">*</span>
                </label>
                <Input
                  value={product.title}
                  onChange={(e) => updateProduct(productIndex, 'title', e.target.value)}
                  placeholder="Product title"
                  className="mt-1"
                />
              </div>

              {/* Description */}
              <div>
                <label className="text-sm font-medium text-white">
                  Description <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={product.description}
                  onChange={(e) => updateProduct(productIndex, 'description', e.target.value)}
                  placeholder="Product description"
                  rows={4}
                  className="mt-1 w-full rounded-md border border-gray-700 bg-[#1A1A1A] px-3 py-2 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-white"
                />
              </div>

              {/* Bullet Points */}
              <div>
                <label className="text-sm font-medium text-white">
                  Bullet Points <span className="text-red-500">*</span>
                </label>
                <div className="space-y-2 mt-1">
                  {product.bullet_points.map((bullet, bulletIndex) => (
                    <div key={bulletIndex} className="flex gap-2">
                      <Input
                        value={bullet}
                        onChange={(e) =>
                          updateBulletPoint(productIndex, bulletIndex, e.target.value)
                        }
                        placeholder={`Bullet point ${bulletIndex + 1}`}
                      />
                      {product.bullet_points.length > 1 && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => removeBulletPoint(productIndex, bulletIndex)}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      )}
                    </div>
                  ))}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => addBulletPoint(productIndex)}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Bullet Point
                  </Button>
                </div>
              </div>

              {/* Optional Fields */}
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium text-white">ASIN</label>
                  <Input
                    value={product.asin}
                    onChange={(e) => updateProduct(productIndex, 'asin', e.target.value)}
                    placeholder="B0XXXXXXX"
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-white">Brand</label>
                  <Input
                    value={product.brand}
                    onChange={(e) => updateProduct(productIndex, 'brand', e.target.value)}
                    placeholder="Brand name"
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-white">Price</label>
                  <Input
                    type="number"
                    step="0.01"
                    value={product.price || ''}
                    onChange={(e) =>
                      updateProduct(productIndex, 'price', parseFloat(e.target.value))
                    }
                    placeholder="29.99"
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-white">Category</label>
                  <Input
                    value={product.category}
                    onChange={(e) => updateProduct(productIndex, 'category', e.target.value)}
                    placeholder="Electronics"
                    className="mt-1"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {/* Add Product Button */}
        <Button type="button" variant="outline" onClick={addProduct} className="w-full">
          <Plus className="h-4 w-4 mr-2" />
          Add Another Product
        </Button>

        {/* Submit */}
        <div className="flex gap-4">
          <Button
            type="submit"
            className="flex-1"
            disabled={importMutation.isPending}
          >
            <Upload className="h-4 w-4 mr-2" />
            {importMutation.isPending ? 'Importing...' : `Import ${products.length} Product${products.length > 1 ? 's' : ''}`}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => router.back()}
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  )
}
