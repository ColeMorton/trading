import {
  UseGlobalFiltersInstanceProps,
  UseGlobalFiltersOptions,
  UsePaginationInstanceProps,
  UsePaginationOptions,
  UsePaginationState,
  UseSortByColumnOptions,
  UseSortByColumnProps,
  UseSortByInstanceProps,
  UseSortByOptions,
  UseSortByState
} from 'react-table';

declare module 'react-table' {
  export interface TableOptions<D extends Record<string, unknown>>
    extends UseGlobalFiltersOptions<D>,
      UsePaginationOptions<D>,
      UseSortByOptions<D> {}

  export interface TableInstance<D extends Record<string, unknown>>
    extends UseGlobalFiltersInstanceProps<D>,
      UsePaginationInstanceProps<D>,
      UseSortByInstanceProps<D> {}

  export interface TableState<D extends Record<string, unknown>>
    extends UsePaginationState<D>,
      UseSortByState<D> {}

  export interface ColumnInterface<D extends Record<string, unknown>>
    extends UseSortByColumnOptions<D> {}

  export interface ColumnInstance<D extends Record<string, unknown>>
    extends UseSortByColumnProps<D> {}
}