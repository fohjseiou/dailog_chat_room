import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '../../test/test-utils';
import {
  Skeleton,
  SkeletonText,
  SkeletonCard,
  SkeletonTable,
  SkeletonChat,
  SkeletonDocument,
} from './Skeleton';

describe('Skeleton', () => {
  it('renders base skeleton with default props', () => {
    const { container } = renderWithProviders(<Skeleton />);
    const skeleton = container.querySelector('.animate-pulse');
    expect(skeleton).toBeInTheDocument();
    expect(skeleton).toHaveClass('bg-gray-200');
  });

  it('applies variant classes', () => {
    const { container: c1 } = renderWithProviders(<Skeleton variant="text" />);
    expect(c1.querySelector('.animate-pulse')).toHaveClass('h-4', 'rounded');

    const { container: c2 } = renderWithProviders(<Skeleton variant="circular" />);
    expect(c2.querySelector('.animate-pulse')).toHaveClass('rounded-full');

    const { container: c3 } = renderWithProviders(<Skeleton variant="rectangular" />);
    expect(c3.querySelector('.animate-pulse')).toHaveClass('rounded-md');
  });

  it('applies custom width and height', () => {
    const { container } = renderWithProviders(
      <Skeleton width="100px" height="50px" />
    );
    const skeleton = container.querySelector('.animate-pulse');
    expect(skeleton).toHaveStyle({ width: '100px', height: '50px' });
  });

  it('applies custom className', () => {
    const { container } = renderWithProviders(<Skeleton className="custom-skeleton" />);
    expect(container.querySelector('.animate-pulse')).toHaveClass('custom-skeleton');
  });
});

describe('SkeletonText', () => {
  it('renders default number of lines', () => {
    const { container } = renderWithProviders(<SkeletonText />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons).toHaveLength(3); // default 3 lines
  });

  it('renders custom number of lines', () => {
    const { container } = renderWithProviders(<SkeletonText lines={5} />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons).toHaveLength(5);
  });

  it('applies custom spacing', () => {
    const { container } = renderWithProviders(<SkeletonText spacing="space-y-4" />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass('space-y-4');
  });
});

describe('SkeletonCard', () => {
  it('renders card skeleton structure', () => {
    const { container } = renderWithProviders(<SkeletonCard />);

    // Check for header, content, and footer skeletons
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders with avatar when showAvatar is true', () => {
    const { container } = renderWithProviders(<SkeletonCard showAvatar />);
    const avatar = container.querySelector('.rounded-full');
    expect(avatar).toBeInTheDocument();
  });

  it('renders with footer actions when showActions is true', () => {
    const { container } = renderWithProviders(<SkeletonCard showActions />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    // Should have more elements for actions
    expect(skeletons.length).toBeGreaterThan(2);
  });
});

describe('SkeletonTable', () => {
  it('renders table with header and rows', () => {
    const { container } = renderWithProviders(<SkeletonTable rows={5} columns={4} />);

    const skeletons = container.querySelectorAll('.animate-pulse');
    // Header (4 columns) + 5 rows * 4 columns = 24 skeletons
    expect(skeletons.length).toBeGreaterThanOrEqual(24);
  });

  it('renders custom number of rows', () => {
    const { container } = renderWithProviders(<SkeletonTable rows={3} columns={3} />);

    // Count total skeleton elements including header
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThanOrEqual(12); // 3 columns + 3*3 rows
  });
});

describe('SkeletonChat', () => {
  it('renders chat message skeletons', () => {
    const { container } = renderWithProviders(<SkeletonChat count={3} />);

    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders custom number of messages', () => {
    const { container: c1 } = renderWithProviders(<SkeletonChat count={2} />);
    const skeletons1 = c1.querySelectorAll('.animate-pulse');

    const { container: c2 } = renderWithProviders(<SkeletonChat count={5} />);
    const skeletons2 = c2.querySelectorAll('.animate-pulse');

    expect(skeletons2.length).toBeGreaterThan(skeletons1.length);
  });
});

describe('SkeletonDocument', () => {
  it('renders document card skeleton', () => {
    const { container } = renderWithProviders(<SkeletonDocument />);

    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders document icon skeleton', () => {
    const { container } = renderWithProviders(<SkeletonDocument />);

    // Check for icon (circular) skeleton
    const iconSkeleton = container.querySelector('.rounded-full');
    expect(iconSkeleton).toBeInTheDocument();
  });

  it('renders with metadata when showMetadata is true', () => {
    const { container: c1 } = renderWithProviders(<SkeletonDocument />);
    const skeletons1 = c1.querySelectorAll('.animate-pulse');

    const { container: c2 } = renderWithProviders(<SkeletonDocument showMetadata />);
    const skeletons2 = c2.querySelectorAll('.animate-pulse');

    expect(skeletons2.length).toBeGreaterThan(skeletons1.length);
  });
});
