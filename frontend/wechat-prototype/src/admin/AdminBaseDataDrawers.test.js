import { describe, expect, it } from 'vitest'
import {
  buildStandardPositionPayload,
  buildTagPayload,
  filterTagParentOptions,
  validateStandardPositionForm,
  validateTagForm,
} from './AdminBaseDataDrawerUtils.js'

describe('base data drawer helpers', () => {
  it('normalizes a standard position form into the API payload', () => {
    expect(buildStandardPositionPayload({
      name: '  Java Engineer  ',
      category: '  Technology ',
      aliasesText: 'Java,  JVM Engineer, ,',
      description: '  Backend role  ',
      status: 'active',
    })).toEqual({
      name: 'Java Engineer',
      category: 'Technology',
      aliases: ['Java', 'JVM Engineer'],
      description: 'Backend role',
      status: 'active',
    })
  })

  it('normalizes a tag form into the API payload', () => {
    expect(buildTagPayload({
      name: '  PeopleSoft ',
      category: ' skill ',
      parentId: '12',
      color: ' #2563eb ',
      description: ' ',
      sortOrder: '7',
      status: 'inactive',
    })).toEqual({
      name: 'PeopleSoft',
      category: 'skill',
      parent_id: 12,
      color: '#2563eb',
      description: null,
      sort_order: 7,
      status: 'inactive',
    })
  })

  it('reports required fields before saving', () => {
    expect(validateStandardPositionForm({ name: ' ', category: '', aliasesText: '', description: '', status: 'active' })).toEqual({
      name: '请填写标准名称',
      category: '请填写分类',
    })
    expect(validateTagForm({ name: '', category: ' ', parentId: '', color: '', description: '', sortOrder: 0, status: 'active' })).toEqual({
      name: '请填写标签名称',
      category: '请填写分类',
    })
  })

  it('rejects fractional tag sort order', () => {
    expect(validateTagForm({
      name: 'PeopleSoft',
      category: 'skill',
      parentId: '',
      color: '',
      description: '',
      sortOrder: '1.5',
      status: 'active',
    })).toEqual({
      sortOrder: '排序必须是非负整数',
    })
  })

  it('excludes the edited tag from parent options', () => {
    const tags = [{ id: 1, name: 'A' }, { id: 2, name: 'B' }]
    expect(filterTagParentOptions(tags, 2)).toEqual([{ id: 1, name: 'A' }])
  })
})
