'use client';

import { Badge, Box, HStack, Wrap } from '@chakra-ui/react';
import { LuLayoutGrid, LuHash, LuCodeXml } from 'react-icons/lu';
import type { IconType } from 'react-icons';

interface ProjectTaxonomyBadgesProps {
  categories: string[];
  tags: string[];
  techStack: string[];
}

interface TaxonomyGroupProps {
  icon: IconType;
  iconColor: string;
  names: string[];
  badgeProps: React.ComponentProps<typeof Badge>;
}

function TaxonomyGroup({
  icon: Icon,
  iconColor,
  names,
  badgeProps,
}: TaxonomyGroupProps) {
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

const categoryBadgeProps: React.ComponentProps<typeof Badge> = {
  bg: 'orange.100',
  color: 'orange.800',
  borderRadius: 'full',
  px: { base: '7px', md: '10px' },
  py: { base: '2px', md: '3px' },
  fontSize: 'xs',
  fontWeight: 'semibold',
  textTransform: 'none',
  letterSpacing: '0.01em',
};

const tagBadgeProps: React.ComponentProps<typeof Badge> = {
  bg: 'white',
  border: '1px solid',
  borderColor: 'orange.200',
  color: 'gray.700',
  borderRadius: '8px',
  px: { base: '7px', md: '10px' },
  py: { base: '2px', md: '3px' },
  fontSize: 'xs',
  fontWeight: 'medium',
  textTransform: 'none',
  letterSpacing: '0.01em',
};

const techBadgeProps: React.ComponentProps<typeof Badge> = {
  bg: 'blue.50',
  color: 'blue.700',
  border: '1px solid',
  borderColor: 'blue.200',
  borderRadius: '6px',
  px: { base: '6px', md: '8px' },
  py: { base: '2px', md: '3px' },
  fontSize: 'xs',
  fontWeight: 'medium',
  textTransform: 'none',
  fontFamily: 'mono',
};

export function ProjectTaxonomyBadges({
  categories,
  tags,
  techStack,
}: ProjectTaxonomyBadgesProps) {
  const hasAny =
    categories.length > 0 || tags.length > 0 || techStack.length > 0;

  if (!hasAny) return null;

  return (
    <>
      {/* Mobile: flat wrap, no group icons */}
      <Wrap gap="6px" display={{ base: 'flex', md: 'none' }}>
        {categories.map((name) => (
          <Badge key={name} {...categoryBadgeProps}>
            {name}
          </Badge>
        ))}
        {tags.map((name) => (
          <Badge key={name} {...tagBadgeProps}>
            {name}
          </Badge>
        ))}
        {techStack.map((name) => (
          <Badge key={name} {...techBadgeProps}>
            {name}
          </Badge>
        ))}
      </Wrap>

      {/* Desktop: grouped with icons */}
      <HStack
        align="center"
        gap="10px"
        w="100%"
        flexWrap="wrap"
        display={{ base: 'none', md: 'flex' }}
      >
        <TaxonomyGroup
          icon={LuLayoutGrid}
          iconColor="orange.600"
          names={categories}
          badgeProps={categoryBadgeProps}
        />
        <TaxonomyGroup
          icon={LuHash}
          iconColor="orange.400"
          names={tags}
          badgeProps={tagBadgeProps}
        />
        <TaxonomyGroup
          icon={LuCodeXml}
          iconColor="blue.500"
          names={techStack}
          badgeProps={techBadgeProps}
        />
      </HStack>
    </>
  );
}
