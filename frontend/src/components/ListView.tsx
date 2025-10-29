import React from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Typography,
  Divider,
  Paper
} from '@mui/material';
import { SpotifyImage } from '../types';

interface ListViewProps {
  items: any[];
  type: 'artists' | 'albums' | 'tracks' | 'playlists';
  getLargestImage: (images: SpotifyImage[]) => string;
  formatDuration?: (ms: number) => string;
}

const ListView: React.FC<ListViewProps> = ({ 
  items, 
  type, 
  getLargestImage,
  formatDuration 
}) => {
  const renderItemContent = (item: any) => {
    switch (type) {
      case 'artists':
        return (
          <>
            <ListItemAvatar>
              <Avatar 
                alt={item.name} 
                src={getLargestImage(item.images)} 
                variant="rounded"
                sx={{ width: 56, height: 56 }}
              />
            </ListItemAvatar>
            <ListItemText
              primary={item.name}
              secondary={
                <>
                  <Typography component="span" variant="body2" color="text.primary">
                    {item.genres.join(', ')}
                  </Typography>
                  <br />
                  <Typography component="span" variant="body2" color="text.secondary">
                    {item.followers.total.toLocaleString()} followers
                  </Typography>
                </>
              }
            />
          </>
        );
      
      case 'albums':
        return (
          <>
            <ListItemAvatar>
              <Avatar 
                alt={item.name} 
                src={getLargestImage(item.images)} 
                variant="rounded"
                sx={{ width: 56, height: 56 }}
              />
            </ListItemAvatar>
            <ListItemText
              primary={item.name}
              secondary={
                <>
                  <Typography component="span" variant="body2" color="text.primary">
                    {item.artists_joined}
                  </Typography>
                  <br />
                  <Typography component="span" variant="body2" color="text.secondary">
                    {item.release_date} • {item.album_type}
                  </Typography>
                </>
              }
            />
          </>
        );
      
      case 'tracks':
        return (
          <>
            <ListItemAvatar>
              <Avatar 
                alt={item.name} 
                src={getLargestImage(item._album.images)} 
                variant="rounded"
                sx={{ width: 56, height: 56 }}
              />
            </ListItemAvatar>
            <ListItemText
              primary={item.name}
              secondary={
                <>
                  <Typography component="span" variant="body2" color="text.primary">
                    {item.artists_joined}
                  </Typography>
                  <br />
                  <Typography component="span" variant="body2" color="text.secondary">
                    {item._album.name} • {formatDuration && formatDuration(item.duration_ms)}
                  </Typography>
                </>
              }
            />
          </>
        );
      
      case 'playlists':
        return (
          <>
            <ListItemAvatar>
              <Avatar 
                alt={item.name} 
                src={getLargestImage(item.images)} 
                variant="rounded"
                sx={{ width: 56, height: 56 }}
              />
            </ListItemAvatar>
            <ListItemText
              primary={item.name}
              secondary={
                <>
                  <Typography component="span" variant="body2" color="text.primary">
                    {item.description}
                  </Typography>
                  <br />
                  <Typography component="span" variant="body2" color="text.secondary">
                    {item.tracks.total} tracks • {item.owner.display_name}
                  </Typography>
                </>
              }
            />
          </>
        );
      
      default:
        return null;
    }
  };

  return (
    <Paper elevation={0} sx={{ mb: 3 }}>
      <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
        {items.map((item, index) => (
          <React.Fragment key={item.id}>
            <ListItem alignItems="flex-start">
              {renderItemContent(item)}
            </ListItem>
            {index < items.length - 1 && <Divider variant="inset" component="li" />}
          </React.Fragment>
        ))}
      </List>
    </Paper>
  );
};

export default ListView; 