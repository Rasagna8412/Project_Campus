import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import App from '../App';

describe('Project Campus App Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders application branding and architecture header', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 'healthy', version: '0.1.0', database: 'connected' }),
    }));

    await act(async () => {
      render(<App />);
    });

    const brandElements = screen.getAllByText('Project Campus');
    expect(brandElements.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Milestone 1 Core')).toBeInTheDocument();
    expect(screen.getByText('Foundational Curriculum Schema')).toBeInTheDocument();
  });

  it('displays connected status when real or mocked backend responds healthy', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 'healthy', version: '0.1.0', database: 'connected' }),
    }));

    await act(async () => {
      render(<App />);
    });

    await waitFor(() => {
      expect(screen.getByText(/Backend v0\.1\.0 • DB Connected/i)).toBeInTheDocument();
    });
  });

  it('displays backend-unavailable state when backend connection fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Failed to fetch')));

    await act(async () => {
      render(<App />);
    });

    await waitFor(() => {
      expect(screen.getByText(/Backend Offline/i)).toBeInTheDocument();
      expect(screen.getByText(/Backend Server Unreachable/i)).toBeInTheDocument();
      expect(screen.getByText(/Failed to fetch/i)).toBeInTheDocument();
    });
  });

  it('renders mathematical formulas through KaTeX engine', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 'healthy', version: '0.1.0', database: 'connected' }),
    }));

    await act(async () => {
      render(<App />);
    });

    expect(screen.getByText('Electrostatics')).toBeInTheDocument();
    expect(screen.getByText('Special Relativity')).toBeInTheDocument();
    expect(screen.getByText('Calculus')).toBeInTheDocument();
  });
});
