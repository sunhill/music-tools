import React, { useState } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Divider
} from '@mui/material';

interface CreatePlaylistProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

type PlaylistType = 'custom' | 'year' | 'decade' | 'random';

const CreatePlaylist: React.FC<CreatePlaylistProps> = ({ open, onClose, onSuccess }) => {
  const [playlistType, setPlaylistType] = useState<PlaylistType>('custom');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [year, setYear] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      let response;
      switch (playlistType) {
        case 'custom':
          response = await fetch('http://localhost:8001/create_playlist', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, description }),
          });
          break;
        case 'year':
          response = await fetch(`http://localhost:8001/playlist_creation/make_playlist_for_year?year=${year}`);
          break;
        case 'decade':
          const startYear = Math.floor(year / 10) * 10;
          const endYear = startYear + 9;
          response = await fetch(`http://localhost:8001/playlist_creation/make_playlists_between_years?start_year=${startYear}&end_year=${endYear}`);
          break;
        case 'random':
          response = await fetch('http://localhost:8001/playlist_creation/make_random_playlist');
          break;
      }

      if (!response?.ok) {
        throw new Error('Failed to create playlist');
      }

      const data = await response.json();
      setName('');
      setDescription('');
      onSuccess?.();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create playlist');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create New Playlist</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Playlist Type</InputLabel>
              <Select
                value={playlistType}
                onChange={(e) => setPlaylistType(e.target.value as PlaylistType)}
                label="Playlist Type"
              >
                <MenuItem value="custom">Custom Playlist</MenuItem>
                <MenuItem value="year">Year Playlist</MenuItem>
                <MenuItem value="decade">Decade Playlist</MenuItem>
                <MenuItem value="random">Random Playlist</MenuItem>
              </Select>
            </FormControl>

            {playlistType === 'custom' && (
              <>
                <TextField
                  label="Playlist Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  fullWidth
                />
                <TextField
                  label="Description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  multiline
                  rows={3}
                  fullWidth
                />
              </>
            )}

            {(playlistType === 'year' || playlistType === 'decade') && (
              <TextField
                label="Year"
                type="number"
                value={year}
                onChange={(e) => setYear(parseInt(e.target.value))}
                required
                fullWidth
                inputProps={{ min: 1900, max: new Date().getFullYear() }}
              />
            )}

            {playlistType === 'random' && (
              <Typography variant="body2" color="text.secondary">
                This will create a random playlist with 1000 songs from your liked tracks and albums.
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={loading || (playlistType === 'custom' && !name)}
          >
            {loading ? <CircularProgress size={24} /> : 'Create Playlist'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default CreatePlaylist; 