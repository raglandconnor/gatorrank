'use client';

import { Badge, Box, HStack } from '@chakra-ui/react';
import { LuLayoutGrid, LuHash, LuCodeXml } from 'react-icons/lu';
import type { IconType } from 'react-icons';

interface ProjectTaxonomyBadgesProps {
  categories: string[];
  tags: string[];
  techStack: string[];
}

interface TaxonomyRowProps {
  icon: IconType;
  iconColor: string;
  names: string[];
  badgeProps: React.ComponentProps<typeof Badge>;
}

function TaxonomyRow({
  icon: Icon,
  iconColor,
  names,
  badgeProps,
}: TaxonomyRowProps) {
  if (!names.length) return null;
  return (
    <HStack gap="6px" align="center" flexWrap="wrap">
      <Box color={iconColor} flexShrink={0}>
        <Icon size={12} />
      </Box>
      {names.map((name) => (
        <Badge key={name} {...badgeProps}>
          {name}
        </Badge>
      ))}
    </HStack>
  );
}

export function ProjectTaxonomyBadges({
  categories,
  tags,
  techStack,
}: ProjectTaxonomyBadgesProps) {
  const hasAny =
    categories.length > 0 || tags.length > 0 || techStack.length > 0;

  if (!hasAny) return null;

  return (
    <HStack align="center" gap="10px" w="100%" flexWrap="wrap">
      <TaxonomyRow
        icon={LuLayoutGrid}
        iconColor="orange.600"
        names={categories}
        badgeProps={{
          bg: 'orange.100',
          color: 'orange.800',
          borderRadius: 'full',
          px: '10px',
          py: '3px',
          fontSize: 'xs',
          fontWeight: 'semibold',
          textTransform: 'none',
          letterSpacing: '0.01em',
        }}
      />
      <TaxonomyRow
        icon={LuHash}
        iconColor="orange.400"
        names={tags}
        badgeProps={{
          bg: 'white',
          border: '1px solid',
          borderColor: 'orange.200',
          color: 'gray.700',
          borderRadius: '8px',
          px: '10px',
          py: '3px',
          fontSize: 'xs',
          fontWeight: 'medium',
          textTransform: 'none',
          letterSpacing: '0.01em',
        }}
      />
      <TaxonomyRow
        icon={LuCodeXml}
        iconColor="blue.500"
        names={techStack}
        badgeProps={{
          bg: 'blue.50',
          color: 'blue.700',
          border: '1px solid',
          borderColor: 'blue.200',
          borderRadius: '6px',
          px: '8px',
          py: '3px',
          fontSize: 'xs',
          fontWeight: 'medium',
          textTransform: 'none',
          fontFamily: 'mono',
        }}
      />
    </HStack>
  );
}
