import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

interface NavbarProps {
  dataDate?: string | null;
}

const Navbar: React.FC<NavbarProps> = ({ dataDate }) => {
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Spotify Export
          {dataDate && (
            <Typography component="span" variant="caption" sx={{ ml: 2, opacity: 0.7 }}>
              (data from {dataDate})
            </Typography>
          )}
        </Typography>
        <Box>
          <Button
            color="inherit"
            component={RouterLink}
            to="/artists"
            sx={{ mx: 1 }}
          >
            Artists
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/albums"
            sx={{ mx: 1 }}
          >
            Albums
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/tracks"
            sx={{ mx: 1 }}
          >
            Tracks
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/playlists"
            sx={{ mx: 1 }}
          >
            Playlists
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar; 